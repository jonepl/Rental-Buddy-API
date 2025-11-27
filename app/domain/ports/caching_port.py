from __future__ import annotations

from typing import Generic, Optional, Protocol, TypeVar

T = TypeVar("T")


class CachePort(Protocol, Generic[T]):
    """
    Port for a simple key/value cache.
    Keys are strings; values are typed domain objects (e.g. Pydantic DTOs).
    """

    async def get(self, key: str) -> Optional[T]:
        """Return cached value or None if not found / expired."""
        ...

    async def set(self, key: str, value: T, ttl_seconds: int | None = None) -> None:
        """Store value under key with optional TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Remove a key from cache (no-op if not present)."""
        ...

    async def clear(self) -> None:
        """Clear all cached entries (implementation-dependent)."""
        ...
