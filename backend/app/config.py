"""
BanglaJudex Configuration Module
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/banglajudex"
    
    # PDF Sources
    ad_judgments_path: Path = Path("./ad_judgments")
    sc_judgments_path: Path = Path("./sc_judgments")
    
    # Vector DB
    chroma_persist_path: Path = Path("./chroma_data")
    
    # LLM
    ollama_host: str = "http://localhost:11434"
    llm_model: str = "mistral"
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Retrieval settings
    retrieval_top_k: int = 10
    confidence_threshold: float = 0.5
    vector_weight: float = 0.5
    keyword_weight: float = 0.3
    statute_weight: float = 0.2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
