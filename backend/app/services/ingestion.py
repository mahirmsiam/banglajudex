"""
PDF Ingestion Service - Handles PDF extraction, OCR, and batch processing.
"""
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models import Case, Paragraph, IngestionLog, IngestionStatus, Court

settings = get_settings()
logger = logging.getLogger(__name__)


class PDFIngestionService:
    """Service for ingesting PDF judgments."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    @staticmethod
    def compute_pdf_hash(pdf_path: Path) -> str:
        """Compute SHA-256 hash of PDF file for deduplication."""
        sha256_hash = hashlib.sha256()
        with open(pdf_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def is_pdf_already_ingested(self, pdf_hash: str) -> bool:
        """Check if PDF has already been ingested."""
        result = await self.db.execute(
            select(IngestionLog).where(
                IngestionLog.pdf_hash == pdf_hash,
                IngestionLog.status == IngestionStatus.COMPLETED
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def get_all_pdfs(self) -> List[Tuple[Path, Court]]:
        """Get all PDF files from both judgment folders."""
        pdfs = []
        
        # Appellate Division judgments
        ad_path = Path(settings.ad_judgments_path)
        if ad_path.exists():
            for pdf_file in ad_path.glob("*.pdf"):
                pdfs.append((pdf_file, Court.APPELLATE_DIVISION))
        
        # High Court / SC judgments
        sc_path = Path(settings.sc_judgments_path)
        if sc_path.exists():
            for pdf_file in sc_path.glob("*.pdf"):
                pdfs.append((pdf_file, Court.HIGH_COURT_DIVISION))
        
        return pdfs
    
    @staticmethod
    def extract_text_from_page(page: fitz.Page) -> str:
        """Extract text from a PDF page, with OCR fallback."""
        # Try direct text extraction first
        text = page.get_text("text")
        
        # If no text found, try OCR
        if not text.strip():
            try:
                # Convert page to image
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # OCR the image
                text = pytesseract.image_to_string(img, lang='eng')
            except Exception as e:
                logger.warning(f"OCR failed for page: {e}")
                text = ""
        
        return text
    
    @staticmethod
    def split_into_paragraphs(text: str, page_no: int) -> List[dict]:
        """Split text into paragraphs with metadata."""
        paragraphs = []
        
        # Split by double newlines or numbered patterns
        lines = text.split('\n')
        current_para = []
        para_no = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_para:
                    para_text = ' '.join(current_para)
                    if len(para_text) > 20:  # Minimum length filter
                        paragraphs.append({
                            "page_no": page_no,
                            "para_no": para_no,
                            "text": para_text,
                            "token_count": len(para_text.split())
                        })
                        para_no += 1
                    current_para = []
            else:
                current_para.append(line)
        
        # Don't forget last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            if len(para_text) > 20:
                paragraphs.append({
                    "page_no": page_no,
                    "para_no": para_no,
                    "text": para_text,
                    "token_count": len(para_text.split())
                })
        
        return paragraphs
    
    def extract_pdf_content(self, pdf_path: Path) -> Tuple[str, List[dict]]:
        """Extract full text and paragraphs from a PDF."""
        all_paragraphs = []
        full_text = ""
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc, start=1):
                page_text = self.extract_text_from_page(page)
                full_text += page_text + "\n\n"
                
                # Split into paragraphs
                page_paragraphs = self.split_into_paragraphs(page_text, page_num)
                all_paragraphs.extend(page_paragraphs)
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}")
            raise
        
        return full_text, all_paragraphs
    
    async def process_single_pdf(
        self, 
        pdf_path: Path, 
        court: Court,
        parsing_service  # Will be injected
    ) -> Optional[Case]:
        """Process a single PDF file."""
        pdf_hash = self.compute_pdf_hash(pdf_path)
        
        # Check if already processed
        if await self.is_pdf_already_ingested(pdf_hash):
            logger.info(f"Skipping already ingested: {pdf_path.name}")
            return None
        
        # Create ingestion log
        log = IngestionLog(
            pdf_name=pdf_path.name,
            pdf_path=str(pdf_path),
            pdf_hash=pdf_hash,
            status=IngestionStatus.PROCESSING
        )
        self.db.add(log)
        await self.db.commit()
        
        try:
            # Extract content (run in thread pool for I/O)
            loop = asyncio.get_event_loop()
            full_text, paragraphs = await loop.run_in_executor(
                self.executor, 
                self.extract_pdf_content, 
                pdf_path
            )
            
            # Parse metadata
            metadata = parsing_service.parse_judgment(full_text, pdf_path.name, court)
            
            # Create case record
            case = Case(
                case_title=metadata.get("case_title", pdf_path.stem),
                case_number=metadata.get("case_number", pdf_path.stem),
                court=court,
                judgment_date=metadata.get("judgment_date"),
                case_type=metadata.get("case_type"),
                outcome=metadata.get("outcome"),
                parties=metadata.get("parties"),
                crime_category=metadata.get("crime_category"),
                source_pdf=pdf_path.name,
                pdf_hash=pdf_hash
            )
            self.db.add(case)
            await self.db.flush()  # Get case ID
            
            # Create paragraph records
            for para_data in paragraphs:
                para = Paragraph(
                    case_id=case.id,
                    page_no=para_data["page_no"],
                    para_no=para_data["para_no"],
                    text=para_data["text"],
                    token_count=para_data.get("token_count"),
                    section_heading=parsing_service.classify_section(para_data["text"])
                )
                self.db.add(para)
            
            # Add judges
            for judge_name in metadata.get("judges", []):
                await parsing_service.add_judge_to_case(self.db, case, judge_name)
            
            # Add statutes
            for statute_info in metadata.get("statutes", []):
                await parsing_service.add_statute_to_case(
                    self.db, case, 
                    statute_info["name"], 
                    statute_info.get("section")
                )
            
            # Update ingestion log
            log.status = IngestionStatus.COMPLETED
            log.pages_processed = len(paragraphs)
            log.paragraphs_extracted = len(paragraphs)
            log.processed_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Successfully ingested: {pdf_path.name}")
            return case
            
        except Exception as e:
            logger.error(f"Failed to ingest {pdf_path.name}: {e}")
            log.status = IngestionStatus.FAILED
            log.error_message = str(e)
            log.processed_at = datetime.utcnow()
            await self.db.commit()
            return None
    
    async def ingest_all(self, parsing_service) -> dict:
        """Ingest all PDFs from both folders."""
        pdfs = await self.get_all_pdfs()
        
        results = {
            "total": len(pdfs),
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for pdf_path, court in pdfs:
            try:
                case = await self.process_single_pdf(pdf_path, court, parsing_service)
                if case:
                    results["completed"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                results["failed"] += 1
        
        return results
    
    async def get_ingestion_status(self) -> dict:
        """Get current ingestion status summary."""
        result = await self.db.execute(select(IngestionLog))
        logs = result.scalars().all()
        
        status = {
            "total_pdfs": len(logs),
            "completed": sum(1 for l in logs if l.status == IngestionStatus.COMPLETED),
            "failed": sum(1 for l in logs if l.status == IngestionStatus.FAILED),
            "pending": sum(1 for l in logs if l.status == IngestionStatus.PENDING),
            "processing": sum(1 for l in logs if l.status == IngestionStatus.PROCESSING)
        }
        
        return status
