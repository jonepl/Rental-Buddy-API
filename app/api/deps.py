from app.core.config import settings
from app.domain.dto.listings import CachedListings
from app.domain.ports.caching_port import CachePort
from app.providers.redis.adapter import RedisModelCacheAdapter
from app.providers.redis.client import get_redis_client
from app.providers.redis.utils import is_redis_connected
from app.providers.rentcast.adapter import RentCastAdapter
from app.providers.rentcast.client import RentCastClient
from app.services.listings_service import ListingsService


async def get_listings_cache() -> CachePort[CachedListings]:
    """
    Construct a Redis-backed cache for normalized listings.
    """
    redis = await get_redis_client()

    if not await is_redis_connected(redis):
        return None

    return RedisModelCacheAdapter(
        redis=redis,
        model_cls=CachedListings,
        prefix=f"{settings.redis_cache_prefix}:listings",
        default_ttl=settings.cache_ttl_seconds,
    )


async def get_listings_service() -> ListingsService:
    client = RentCastClient()
    adapter = RentCastAdapter(client)
    cache = await get_listings_cache()

    return ListingsService(
        listings_port=adapter,
        cache_port=cache,
    )
