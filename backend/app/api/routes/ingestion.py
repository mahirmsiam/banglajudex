"""
Ingestion API Routes
"""
import asyncio
from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import IngestionLog
from app.schemas import (
    IngestionStatusResponse, IngestionTriggerResponse, IngestionLogResponse
)
from app.services import PDFIngestionService, JudgmentParsingService, embedding_service

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


async def run_ingestion(db: AsyncSession):
    """Background task to run PDF ingestion."""
    ingestion_service = PDFIngestionService(db)
    parsing_service = JudgmentParsingService()
    
    # Get all PDFs
    pdfs = await ingestion_service.get_all_pdfs()
    
    for pdf_path, court in pdfs:
        try:
            case = await ingestion_service.process_single_pdf(
                pdf_path, court, parsing_service
            )
            
            if case:
                # Generate embeddings for paragraphs
                paragraphs = case.paragraphs
                if paragraphs:
                    paragraph_ids = [str(p.id) for p in paragraphs]
                    texts = [p.text for p in paragraphs]
                    metadatas = [
                        {
                            "case_id": str(case.id),
                            "court": case.court.value,
                            "case_type": case.case_type.value if case.case_type else "other",
                            "outcome": case.outcome.value if case.outcome else "other",
                            "year": case.judgment_date.year if case.judgment_date else 0,
                            "page_no": p.page_no,
                            "para_no": p.para_no
                        }
                        for p in paragraphs
                    ]
                    
                    embedding_service.add_paragraphs(
                        paragraph_ids=paragraph_ids,
                        texts=texts,
                        metadatas=metadatas
                    )
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            continue


@router.post("/start", response_model=IngestionTriggerResponse)
async def start_ingestion(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger PDF ingestion process.
    
    This starts a background task that:
    1. Scans both PDF folders
    2. Extracts text (with OCR fallback)
    3. Parses metadata
    4. Generates embeddings
    5. Stores in database and vector store
    
    Ingestion is idempotent - already processed PDFs are skipped.
    """
    ingestion_service = PDFIngestionService(db)
    pdfs = await ingestion_service.get_all_pdfs()
    
    # Start background task
    background_tasks.add_task(run_ingestion, db)
    
    return IngestionTriggerResponse(
        message="Ingestion started in background",
        total_to_process=len(pdfs)
    )


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    db: AsyncSession = Depends(get_db)
):
    """Get current ingestion status summary."""
    ingestion_service = PDFIngestionService(db)
    status = await ingestion_service.get_ingestion_status()
    
    return IngestionStatusResponse(**status)


@router.get("/logs", response_model=List[IngestionLogResponse])
async def get_ingestion_logs(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get ingestion logs with optional status filter."""
    query = select(IngestionLog)
    
    if status:
        query = query.where(IngestionLog.status == status)
    
    query = query.offset(skip).limit(limit).order_by(IngestionLog.created_at.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs


@router.get("/vector-stats")
async def get_vector_stats():
    """Get vector store statistics."""
    stats = embedding_service.get_stats()
    return stats
