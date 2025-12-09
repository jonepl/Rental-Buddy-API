"""Test configuration and global fixtures."""

from __future__ import annotations

import sys
import types


def _ensure_redis_stub() -> None:
    if "redis" in sys.modules:
        return

    redis_module = types.ModuleType("redis")
    redis_async_module = types.ModuleType("redis.asyncio")
    redis_exceptions_module = types.ModuleType("redis.exceptions")

    class _DummyRedisError(Exception):
        pass

    class _DummyRedis:  # pragma: no cover - lightweight stub
        @classmethod
        def from_url(cls, *_args, **_kwargs):
            return cls()

        async def get(self, *_args, **_kwargs):
            return None

        async def set(self, *_args, **_kwargs):
            return None

        async def delete(self, *_args, **_kwargs):
            return None

        async def scan(self, *_args, **_kwargs):
            return 0, []

    redis_async_module.Redis = _DummyRedis
    redis_async_module.RedisError = _DummyRedisError
    redis_async_module.ConnectionError = _DummyRedisError
    redis_async_module.TimeoutError = _DummyRedisError

    redis_exceptions_module.RedisError = _DummyRedisError
    redis_exceptions_module.ConnectionError = _DummyRedisError
    redis_exceptions_module.TimeoutError = _DummyRedisError

    redis_module.asyncio = redis_async_module
    redis_module.exceptions = redis_exceptions_module

    sys.modules["redis"] = redis_module
    sys.modules["redis.asyncio"] = redis_async_module
    sys.modules["redis.exceptions"] = redis_exceptions_module


_ensure_redis_stub()
