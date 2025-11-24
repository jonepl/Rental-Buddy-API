# app/providers/cache/redis_cache_adapter.py
from __future__ import annotations

import logging
from typing import Generic, Optional, Type, TypeVar, Callable, Any

from pydantic import BaseModel
from redis.asyncio import Redis

from app.domain.ports.caching_port import CachePort
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class RedisModelCacheAdapter(CachePort[T], Generic[T]):
    """
    Redis-backed cache for Pydantic models.

    - Keys: str, namespaced with a prefix
    - Values: Pydantic models serialized as JSON
    """

    def __init__(
        self,
        redis: Redis,
        model_cls: Type[T],
        prefix: str,
        default_ttl: int | None = None,
        # Optional custom serializer/deserializer if you ever need them:
        serializer: Callable[[T], str] | None = None,
        deserializer: Callable[[str], T] | None = None,
    ) -> None:
        self._redis = redis
        self._model_cls = model_cls
        self._prefix = prefix.rstrip(":")
        self._default_ttl = default_ttl or settings.cache_ttl_seconds
        self._serializer = serializer or self._default_serialize
        self._deserializer = deserializer or self._default_deserialize

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def _default_serialize(self, value: T) -> str:
        # Pydantic v2 uses model_dump_json; v1 uses json().
        if hasattr(value, "model_dump_json"):
            return value.model_dump_json()
        return value.json()

    def _default_deserialize(self, raw: str) -> T:
        # Pydantic v2 uses model_validate_json; v1 uses parse_raw.
        if hasattr(self._model_cls, "model_validate_json"):
            return self._model_cls.model_validate_json(raw)
        return self._model_cls.parse_raw(raw)

    async def get(self, key: str) -> Optional[T]:
        full_key = self._key(key)
        raw = await self._redis.get(full_key)
        if raw is None:
            logger.debug("Redis cache MISS: %s", full_key)
            return None

        try:
            if isinstance(raw, bytes):
                raw_str = raw.decode("utf-8")
            else:
                raw_str = raw  # decode_responses=False but just in case
            value = self._deserializer(raw_str)
            logger.debug("Redis cache HIT: %s", full_key)
            return value
        except Exception:
            logger.exception("Failed to deserialize cached value for key: %s", full_key)
            # Optionally delete corrupt entry
            await self._redis.delete(full_key)
            return None

    async def set(self, key: str, value: T, ttl_seconds: int | None = None) -> None:
        full_key = self._key(key)
        raw = self._serializer(value)
        ttl = ttl_seconds or self._default_ttl

        await self._redis.set(full_key, raw, ex=ttl)
        logger.debug("Redis cache SET: %s (ttl=%s)", full_key, ttl)

    async def delete(self, key: str) -> None:
        full_key = self._key(key)
        await self._redis.delete(full_key)
        logger.debug("Redis cache DELETE: %s", full_key)

    async def clear(self) -> None:
        """
        Clear all keys for this prefix (prefix scan).
        Be careful in production — this is namespaced but still potentially large.
        """
        pattern = f"{self._prefix}:*"
        cursor: int | str = 0
        while True:
            cursor, keys = await self._redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break
        logger.info("Redis cache CLEARED for prefix: %s", self._prefix)
