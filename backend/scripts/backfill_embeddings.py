
import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.db import async_session_maker
from app.models import Case, Paragraph
from app.services.embeddings import embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backfill_embeddings():
    """Backfill embeddings for all cases in the database."""
    logger.info("Starting embedding backfill...")
    
    async with async_session_maker() as db:
        # Get all cases with paragraphs
        result = await db.execute(
            select(Case).options(
                selectinload(Case.paragraphs)
            )
        )
        cases = result.scalars().all()
        logger.info(f"Found {len(cases)} cases to process.")
        
        for i, case in enumerate(cases):
            if not case.paragraphs:
                continue
                
            try:
                # Prepare data
                para_ids = [str(p.id) for p in case.paragraphs]
                texts = [p.text for p in case.paragraphs]
                metadatas = [{
                    "case_id": str(case.id),
                    "court": case.court.value,
                    "year": case.judgment_date.year if case.judgment_date else 0,
                    "case_type": case.case_type.value if case.case_type else "unknown",
                    "outcome": case.outcome.value if case.outcome else "unknown",
                    "page_no": p.page_no,
                    "para_no": p.para_no,
                    "section_heading": p.section_heading.value
                } for p in case.paragraphs]
                
                # Check if already in Chroma (simple check by ID)
                # Optimization: For now just overwrite/add. 
                # ChromaDB handles upserts.
                
                # Add to vector store
                embedding_service.add_paragraphs(para_ids, texts, metadatas)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(cases)} cases...")
                    
            except Exception as e:
                logger.error(f"Error processing case {case.case_number}: {e}")
                
    logger.info("Backfill complete!")

if __name__ == "__main__":
    asyncio.run(backfill_embeddings())
