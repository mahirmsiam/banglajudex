"""
Health Check API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db import get_db
from app.schemas import HealthResponse
from app.services import embedding_service, llm_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    Health check endpoint.
    
    Checks:
    - Database connectivity
    - Vector database availability
    - LLM service availability
    """
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check vector DB
    try:
        embedding_service.get_stats()
        vector_status = "healthy"
    except Exception as e:
        vector_status = f"unhealthy: {str(e)}"
    
    # Check LLM
    try:
        is_healthy = await llm_service.check_health()
        llm_status = "healthy" if is_healthy else "unhealthy"
    except Exception as e:
        llm_status = f"unhealthy: {str(e)}"
    
    overall = "healthy"
    if "unhealthy" in db_status or "unhealthy" in vector_status:
        overall = "degraded"
    
    return HealthResponse(
        status=overall,
        database=db_status,
        vector_db=vector_status,
        llm=llm_status
    )


@router.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "BanglaJudex API",
        "version": "1.0.0",
        "description": "Extractive Legal Research System for Bangladesh Judgments",
        "docs": "/docs"
    }
