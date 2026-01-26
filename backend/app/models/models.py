"""
SQLAlchemy models for BanglaJudex database schema.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
import enum

from sqlalchemy import (
    String, Text, DateTime, Integer, Float, ForeignKey, 
    Enum, UniqueConstraint, Index, Table, Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class CaseType(enum.Enum):
    """Case type enumeration."""
    CIVIL = "civil"
    CRIMINAL = "criminal"
    REVISION = "revision"
    APPEAL = "appeal"
    WRIT = "writ"
    CONTEMPT = "contempt"
    REVIEW = "review"
    OTHER = "other"


class Outcome(enum.Enum):
    """Case outcome enumeration."""
    ALLOWED = "allowed"
    DISMISSED = "dismissed"
    REMANDED = "remanded"
    CONFIRMED = "confirmed"
    DISPOSED = "disposed"
    DISCHARGED = "discharged"
    OTHER = "other"


class Court(enum.Enum):
    """Court enumeration."""
    APPELLATE_DIVISION = "appellate_division"
    HIGH_COURT_DIVISION = "high_court_division"


class IngestionStatus(enum.Enum):
    """PDF ingestion status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Association table for case-judge many-to-many relationship
case_judges = Table(
    "case_judges",
    Base.metadata,
    Column("case_id", UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("judge_id", UUID(as_uuid=True), ForeignKey("judges.id", ondelete="CASCADE"), primary_key=True)
)

# Association table for case-statute many-to-many relationship
case_statutes = Table(
    "case_statutes",
    Base.metadata,
    Column("case_id", UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("statute_id", UUID(as_uuid=True), ForeignKey("statutes.id", ondelete="CASCADE"), primary_key=True)
)


class Case(Base):
    """Judgment case model."""
    __tablename__ = "cases"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_title: Mapped[str] = mapped_column(String(500), nullable=False)
    case_number: Mapped[str] = mapped_column(String(100), nullable=False)
    court: Mapped[Court] = mapped_column(Enum(Court), nullable=False)
    judgment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    case_type: Mapped[Optional[CaseType]] = mapped_column(Enum(CaseType), nullable=True)
    outcome: Mapped[Optional[Outcome]] = mapped_column(Enum(Outcome), nullable=True)
    parties: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    crime_category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_pdf: Mapped[str] = mapped_column(String(500), nullable=False)
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    judges: Mapped[List["Judge"]] = relationship(secondary=case_judges, back_populates="cases")
    statutes: Mapped[List["Statute"]] = relationship(secondary=case_statutes, back_populates="cases")
    paragraphs: Mapped[List["Paragraph"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_case_number", "case_number"),
        Index("idx_court", "court"),
        Index("idx_judgment_date", "judgment_date"),
        Index("idx_case_type", "case_type"),
        Index("idx_outcome", "outcome"),
    )


class Judge(Base):
    """Judge model."""
    __tablename__ = "judges"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cases: Mapped[List["Case"]] = relationship(secondary=case_judges, back_populates="judges")


class Statute(Base):
    """Statute reference model."""
    __tablename__ = "statutes"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    statute_name: Mapped[str] = mapped_column(String(300), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cases: Mapped[List["Case"]] = relationship(secondary=case_statutes, back_populates="statutes")
    
    __table_args__ = (
        UniqueConstraint("statute_name", "section", name="uq_statute_section"),
        Index("idx_statute_name", "statute_name"),
        Index("idx_section", "section"),
    )


class SectionHeading(enum.Enum):
    """Logical section headings in judgments."""
    FACTS = "facts"
    ISSUES = "issues"
    SUBMISSIONS = "submissions"
    FINDINGS = "findings"
    DECISION = "decision"
    ORDER = "order"
    UNKNOWN = "unknown"


class Paragraph(Base):
    """Paragraph model - core retrieval unit."""
    __tablename__ = "paragraphs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    para_no: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[Optional[SectionHeading]] = mapped_column(Enum(SectionHeading), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case: Mapped["Case"] = relationship(back_populates="paragraphs")
    
    __table_args__ = (
        Index("idx_case_paragraph", "case_id", "page_no", "para_no"),
        Index("idx_section_heading", "section_heading"),
    )


class IngestionLog(Base):
    """PDF ingestion log model."""
    __tablename__ = "ingestion_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pdf_name: Mapped[str] = mapped_column(String(500), nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(500), nullable=False)
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus), default=IngestionStatus.PENDING)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pages_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    paragraphs_extracted: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_pdf_hash", "pdf_hash"),
        Index("idx_ingestion_status", "status"),
    )
