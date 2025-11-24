import redis
from redis.asyncio import Redis

async def is_redis_connected(redis_client: Redis) -> bool:
    try:
        return await redis_client.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        return False
    except Exception:
        return False
