"""API Routes package."""
from fastapi import APIRouter

from app.api.routes import search, ingestion, health

router = APIRouter()

# Include all route modules
router.include_router(search.router)
router.include_router(ingestion.router)
router.include_router(health.router)
