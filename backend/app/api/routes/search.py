"""
Search and Query API Routes
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Case, Paragraph
from app.schemas import (
    SearchRequest, SearchResponse, SearchFilters,
    QueryRequest, QueryResponse,
    CaseResponse, CaseDetailResponse, ParagraphResponse,
    FilterOptions
)
from app.services import RetrievalService, llm_service

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_judgments(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform hybrid search across judgments.
    
    Combines:
    - Vector similarity search
    - Keyword matching
    - Statute/section matching
    
    With optional structured filters.
    """
    retrieval = RetrievalService(db)
    
    results = await retrieval.search(
        query=request.query,
        filters=request.filters,
        top_k=request.top_k
    )
    
    return SearchResponse(
        query=request.query,
        results=results,
        total_found=len(results),
        filters_applied=request.filters
    )


@router.post("/query", response_model=QueryResponse)
async def conversational_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Conversational query with extractive LLM answering.
    
    The system will:
    1. Retrieve relevant paragraphs
    2. Generate an extractive answer grounded in the text
    3. Include citations for all referenced content
    
    If no relevant content is found, a mandatory refusal is returned.
    """
    retrieval = RetrievalService(db)
    
    # Retrieve relevant paragraphs
    results = await retrieval.search(
        query=request.query,
        filters=request.filters,
        top_k=10
    )
    
    # Generate extractive answer
    answer = await llm_service.generate_answer(
        query=request.query,
        results=results,
        filters=request.filters.model_dump() if request.filters else None,
        conversation_history=request.conversation_history
    )
    
    # Extract citations
    citations = llm_service.extract_citations(results)
    
    return QueryResponse(
        answer=answer,
        citations=citations,
        retrieved_paragraphs=results
    )


@router.get("/cases", response_model=List[CaseResponse])
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    court: Optional[str] = None,
    year: Optional[int] = None,
    case_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List cases with optional filtering and pagination."""
    query = select(Case).options(
        selectinload(Case.judges),
        selectinload(Case.statutes)
    )
    
    if court:
        query = query.where(Case.court == court)
    
    if case_type:
        query = query.where(Case.case_type == case_type)
    
    query = query.offset(skip).limit(limit).order_by(Case.created_at.desc())
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return cases


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed case information including paragraphs."""
    result = await db.execute(
        select(Case).options(
            selectinload(Case.judges),
            selectinload(Case.statutes),
            selectinload(Case.paragraphs)
        ).where(Case.id == case_id)
    )
    
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return case


@router.get("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def get_paragraph(
    paragraph_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific paragraph."""
    result = await db.execute(
        select(Paragraph).where(Paragraph.id == paragraph_id)
    )
    
    paragraph = result.scalar_one_or_none()
    
    if not paragraph:
        raise HTTPException(status_code=404, detail="Paragraph not found")
    
    return paragraph


@router.get("/filters", response_model=FilterOptions)
async def get_filter_options(
    db: AsyncSession = Depends(get_db)
):
    """Get available filter options from the database."""
    retrieval = RetrievalService(db)
    options = await retrieval.get_filter_options()
    
    return FilterOptions(**options)
