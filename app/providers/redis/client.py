from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """
    Lazily create a singleton async Redis client.
    """
    global _redis_client
    if _redis_client is None:
        logger.info("Initializing Redis client: %s", settings.redis_url)
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=False)
    return _redis_client


async def close_redis_client() -> None:
    """
    Close the Redis connection (useful for test teardown / app shutdown).
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        await _redis_client.wait_closed()
        _redis_client = None
