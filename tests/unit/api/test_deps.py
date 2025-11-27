from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

import pytest

from app.api import deps
from app.api.deps import get_listings_cache, get_listings_service
from app.domain.dto import CachedListings
from app.providers.redis.adapter import RedisModelCacheAdapter
from app.services.listings_service import ListingsService


@pytest.mark.asyncio
@patch("app.api.deps.get_redis_client")
@patch("app.api.deps.is_redis_connected")
@patch("app.api.deps.RedisModelCacheAdapter")
async def test_get_listings_cache_builds_adapter(
    mock_adapter_cls, mock_is_redis_connected, mock_get_redis_client
):
    redis = MagicMock()
    mock_get_redis_client.return_value = redis
    mock_is_redis_connected.return_value = True

    cache = await get_listings_cache()

    assert cache is not None
    mock_adapter_cls.assert_called_once_with(
        redis=redis,
        model_cls=CachedListings,
        prefix=ANY,
        default_ttl=ANY,
    )


@pytest.mark.asyncio
@patch("app.api.deps.get_redis_client")
@patch("app.api.deps.is_redis_connected")
@patch("app.api.deps.RedisModelCacheAdapter")
async def test_get_listings_cache_returns_none_when_redis_is_not_connected(
    mock_adapter_cls, mock_is_redis_connected, mock_get_redis_client
):
    mock_get_redis_client.return_value = None
    mock_is_redis_connected.return_value = False

    cache = await get_listings_cache()

    assert cache is None
    mock_adapter_cls.assert_not_called()


@pytest.mark.asyncio
@patch("app.api.deps.get_listings_cache")
@patch("app.api.deps.RentCastAdapter")
@patch("app.api.deps.RentCastClient")
async def test_get_listings_service_returns_args(
    mock_rentcast_client, mock_rentcast_adapter, mock_get_listings_cache
):
    mock_rentcast_client.return_value = MagicMock()
    mock_rentcast_adapter.return_value = MagicMock()
    mock_get_listings_cache.return_value = MagicMock()

    service = await get_listings_service()

    assert service.cache is mock_get_listings_cache.return_value
    assert service.listings_port is mock_rentcast_adapter.return_value
