"""
BanglaJudex - Main FastAPI Application
Extractive Conversational Legal Research System for Bangladesh Judgments
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db, close_db
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting BanglaJudex API...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BanglaJudex API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="BanglaJudex API",
    description="""
    ## Extractive Conversational Legal Research System for Bangladesh Judgments
    
    A production-grade API for querying Bangladesh Supreme Court judgments.
    
    ### Features
    - **Hybrid Search**: Vector similarity + keyword matching + statute detection
    - **Citation-First**: Every answer includes Case Title, Case Number, Page, Paragraph
    - **Extractive AI**: Answers grounded in judgment text, no interpretation
    - **Structured Filters**: Filter by court, year, judge, case type, outcome
    
    ### Constraints
    - Only uses PDFs from designated folders
    - No legal advice or interpretation
    - Mandatory refusal when evidence is insufficient
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
