from redis.asyncio import Redis

async def get_redis_stats(redis: Redis) -> dict:
    """
    Get Redis statistics.
    """
    # if redis is None or redis.connection_pool is None:
    #     return {"error": "Redis client is not initialized"}
    try:
        info = await redis.info("stats")
        memory = await redis.info("memory")
    except Exception as e:
        return {"error": f"Failed to get Redis stats: {str(e)}"}

    return {
        "hits": info.get("keyspace_hits", 0),
        "misses": info.get("keyspace_misses", 0),
        "hit_rate": compute_hit_rate(info),
        "evicted_keys": info.get("evicted_keys", 0),
        "expired_keys": info.get("expired_keys", 0),
        "used_memory_human": memory.get("used_memory_human"),
    }


def compute_hit_rate(info: dict) -> float:
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    return hits / total if total > 0 else 0.0
