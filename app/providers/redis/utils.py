import logging

from redis.asyncio import ConnectionError, Redis, TimeoutError

logger = logging.getLogger(__name__)


async def is_redis_connected(redis_client: Redis) -> bool:
    try:
        return await redis_client.ping()
    except (ConnectionError, TimeoutError) as e:
        logger.error("Failed to connect to Redis: %s", e)
        return False
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", e)
        return False
