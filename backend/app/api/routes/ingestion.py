"""
Ingestion API Routes
"""
import asyncio
from typing import List
import logging

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db, async_session_maker
from app.models import IngestionLog
from app.schemas import (
    IngestionStatusResponse, IngestionTriggerResponse, IngestionLogResponse
)
from app.services import PDFIngestionService, JudgmentParsingService, embedding_service

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)

# Track ingestion status
ingestion_status = {
    "is_running": False,
    "total_files": 0,
    "processed": 0,
    "successful": 0,
    "failed": 0,
    "current_file": None
}


async def run_ingestion_task():
    """Background task to run PDF ingestion with its own database session."""
    global ingestion_status
    
    ingestion_status["is_running"] = True
    ingestion_status["processed"] = 0
    ingestion_status["successful"] = 0
    ingestion_status["failed"] = 0
    
    # Create our own database session for the background task
    async with async_session_maker() as db:
        ingestion_service = PDFIngestionService(db)
        parsing_service = JudgmentParsingService()
        
        # Get all PDFs
        pdfs = await ingestion_service.get_all_pdfs()
        ingestion_status["total_files"] = len(pdfs)
        
        for pdf_path, court in pdfs:
            ingestion_status["current_file"] = pdf_path.name if hasattr(pdf_path, 'name') else str(pdf_path)
            ingestion_status["processed"] += 1
            
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
                    
                    ingestion_status["successful"] += 1
                    await db.commit()
                    
            except Exception as e:
                ingestion_status["failed"] += 1
                logger.error(f"Error processing {pdf_path}: {e}")
                await db.rollback()
                continue
            
            # Log progress every 100 files
            if ingestion_status["processed"] % 100 == 0:
                logger.info(f"Ingestion progress: {ingestion_status['processed']}/{ingestion_status['total_files']}")
    
    ingestion_status["is_running"] = False
    ingestion_status["current_file"] = None
    logger.info(f"Ingestion complete: {ingestion_status['successful']} successful, {ingestion_status['failed']} failed")


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
    global ingestion_status
    
    if ingestion_status["is_running"]:
        return IngestionTriggerResponse(
            message="Ingestion already in progress",
            total_to_process=ingestion_status["total_files"]
        )
    
    ingestion_service = PDFIngestionService(db)
    pdfs = await ingestion_service.get_all_pdfs()
    
    # Start background task with its own session
    background_tasks.add_task(run_ingestion_task)
    
    return IngestionTriggerResponse(
        message="Ingestion started in background",
        total_to_process=len(pdfs)
    )


@router.get("/status")
async def get_ingestion_status_live():
    """Get current ingestion status (live from memory)."""
    return {
        "is_running": ingestion_status["is_running"],
        "total_files": ingestion_status["total_files"],
        "processed": ingestion_status["processed"],
        "successful": ingestion_status["successful"],
        "failed": ingestion_status["failed"],
        "current_file": ingestion_status["current_file"],
        "percentage": (ingestion_status["processed"] / ingestion_status["total_files"] * 100) if ingestion_status["total_files"] > 0 else 0
    }


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
