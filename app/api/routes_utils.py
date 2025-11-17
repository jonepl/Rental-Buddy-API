import logging
from typing import List, Optional

from fastapi import APIRouter

from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances
cache_service = CacheService()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rental-buddy"}


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics (for debugging)"""
    return cache_service.get_stats()
