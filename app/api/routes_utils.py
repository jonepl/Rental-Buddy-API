import logging
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.providers.redis.client import get_redis_client
from app.providers.redis.stats import get_redis_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rental-buddy"}


@router.get("/cache/stats")
async def get_cache_stats(redis: Redis = Depends(get_redis_client)):
    """Get cache statistics (for debugging)"""
    return await get_redis_stats(redis)
