from redis.asyncio import Redis, ConnectionError, TimeoutError
import logging

logger = logging.getLogger(__name__)

async def is_redis_connected(redis_client: Redis) -> bool:
    try:
        return await redis_client.ping()
    except (ConnectionError, TimeoutError):
        logger.error("Failed to connect to Redis: %s", e)
        return False
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", e)
        return False
