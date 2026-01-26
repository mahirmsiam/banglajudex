"""
Embedding Service - Generates and manages text embeddings.
"""
import logging
from typing import List, Optional
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and storing embeddings."""
    
    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        self._chroma_client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model
    
    @property
    def chroma_client(self) -> chromadb.Client:
        """Lazy load ChromaDB client."""
        if self._chroma_client is None:
            persist_path = Path(settings.chroma_persist_path)
            persist_path.mkdir(parents=True, exist_ok=True)
            
            self._chroma_client = chromadb.PersistentClient(
                path=str(persist_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._chroma_client
    
    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the paragraphs collection."""
        if self._collection is None:
            self._collection = self.chroma_client.get_or_create_collection(
                name="paragraphs",
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.model.encode(text, normalize_embeddings=True).tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(
            texts, 
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=32
        )
        return embeddings.tolist()
    
    def add_paragraphs(
        self,
        paragraph_ids: List[str],
        texts: List[str],
        metadatas: List[dict]
    ) -> None:
        """Add paragraphs with embeddings to ChromaDB."""
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(paragraph_ids), batch_size):
            end_idx = min(i + batch_size, len(paragraph_ids))
            
            self.collection.add(
                ids=paragraph_ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        
        logger.info(f"Added {len(paragraph_ids)} paragraphs to vector store")
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None
    ) -> dict:
        """
        Search for similar paragraphs.
        
        Returns:
            dict with keys: ids, distances, documents, metadatas
        """
        query_embedding = self.generate_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else []
        }
    
    def delete_by_case(self, case_id: str) -> None:
        """Delete all paragraphs for a case."""
        self.collection.delete(
            where={"case_id": case_id}
        )
    
    def get_stats(self) -> dict:
        """Get collection statistics."""
        return {
            "total_paragraphs": self.collection.count(),
            "collection_name": self.collection.name
        }
    
    def reset(self) -> None:
        """Reset the entire collection."""
        self.chroma_client.delete_collection("paragraphs")
        self._collection = None
        logger.warning("Vector store collection reset")


# Singleton instance
embedding_service = EmbeddingService()
