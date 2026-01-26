"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models import CaseType, Outcome, Court, SectionHeading, IngestionStatus


# ===== Base Schemas =====

class JudgeBase(BaseModel):
    """Base judge schema."""
    name: str


class JudgeResponse(JudgeBase):
    """Judge response schema."""
    id: UUID
    
    class Config:
        from_attributes = True


class StatuteBase(BaseModel):
    """Base statute schema."""
    statute_name: str
    section: Optional[str] = None


class StatuteResponse(StatuteBase):
    """Statute response schema."""
    id: UUID
    
    class Config:
        from_attributes = True


class ParagraphBase(BaseModel):
    """Base paragraph schema."""
    page_no: int
    para_no: int
    section_heading: Optional[SectionHeading] = None
    text: str


class ParagraphResponse(ParagraphBase):
    """Paragraph response schema."""
    id: UUID
    case_id: UUID
    token_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class CaseBase(BaseModel):
    """Base case schema."""
    case_title: str
    case_number: str
    court: Court
    judgment_date: Optional[datetime] = None
    case_type: Optional[CaseType] = None
    outcome: Optional[Outcome] = None
    parties: Optional[str] = None
    crime_category: Optional[str] = None


class CaseResponse(CaseBase):
    """Case response schema."""
    id: UUID
    source_pdf: str
    created_at: datetime
    judges: List[JudgeResponse] = []
    statutes: List[StatuteResponse] = []
    
    class Config:
        from_attributes = True


class CaseDetailResponse(CaseResponse):
    """Detailed case response with paragraphs."""
    paragraphs: List[ParagraphResponse] = []


# ===== Search Schemas =====

class SearchFilters(BaseModel):
    """Search filter parameters."""
    court: Optional[Court] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    judge: Optional[str] = None
    case_type: Optional[CaseType] = None
    outcome: Optional[Outcome] = None
    statute_name: Optional[str] = None
    section: Optional[str] = None
    crime_category: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request schema."""
    query: str = Field(..., min_length=3, max_length=1000)
    filters: Optional[SearchFilters] = None
    top_k: int = Field(default=10, ge=1, le=50)


class Citation(BaseModel):
    """Citation format for retrieved paragraphs."""
    case_title: str
    case_number: str
    page_no: int
    para_no: int
    court: Court


class SearchResult(BaseModel):
    """Individual search result."""
    paragraph_id: UUID
    case_id: UUID
    text: str
    citation: Citation
    score: float
    section_heading: Optional[SectionHeading] = None


class SearchResponse(BaseModel):
    """Search response schema."""
    query: str
    results: List[SearchResult]
    total_found: int
    filters_applied: Optional[SearchFilters] = None


# ===== Query Schemas =====

class ConversationMessage(BaseModel):
    """Single conversation message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class QueryRequest(BaseModel):
    """Conversational query request."""
    query: str = Field(..., min_length=3, max_length=1000)
    filters: Optional[SearchFilters] = None
    conversation_history: List[ConversationMessage] = []


class QueryResponse(BaseModel):
    """Conversational query response."""
    answer: str
    citations: List[Citation]
    retrieved_paragraphs: List[SearchResult]
    conversation_id: Optional[str] = None


# ===== Ingestion Schemas =====

class IngestionLogResponse(BaseModel):
    """Ingestion log response schema."""
    id: UUID
    pdf_name: str
    status: IngestionStatus
    error_message: Optional[str] = None
    pages_processed: Optional[int] = None
    paragraphs_extracted: Optional[int] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class IngestionStatusResponse(BaseModel):
    """Overall ingestion status."""
    total_pdfs: int
    completed: int
    failed: int
    pending: int
    processing: int


class IngestionTriggerResponse(BaseModel):
    """Response when triggering ingestion."""
    message: str
    total_to_process: int


# ===== Filter Options =====

class FilterOptions(BaseModel):
    """Available filter options."""
    courts: List[str]
    years: List[int]
    judges: List[str]
    case_types: List[str]
    outcomes: List[str]
    statutes: List[str]
    crime_categories: List[str]


# ===== Health Check =====

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    vector_db: str
    llm: str
