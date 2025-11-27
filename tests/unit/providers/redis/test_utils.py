from unittest.mock import AsyncMock, patch

import pytest
from redis.exceptions import ConnectionError, TimeoutError

from app.providers.redis.utils import is_redis_connected


@pytest.mark.asyncio
async def test_is_redis_connected_success():
    """Test successful Redis connection check."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    result = await is_redis_connected(mock_redis)

    assert result is True
    mock_redis.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_redis_connected_connection_error():
    """Test Redis connection check with connection error."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("Connection failed"))

    with patch("app.providers.redis.utils.logger") as mock_logger:
        result = await is_redis_connected(mock_redis)

        assert result is False
        mock_redis.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_redis_connected_timeout_error():
    """Test Redis connection check with timeout error."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=TimeoutError("Operation timed out"))

    with patch("app.providers.redis.utils.logger") as mock_logger:
        result = await is_redis_connected(mock_redis)

        assert result is False
        mock_redis.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_redis_connected_unexpected_error():
    """Test Redis connection check with unexpected error."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("Unexpected error"))

    with patch("app.providers.redis.utils.logger") as mock_logger:
        result = await is_redis_connected(mock_redis)

        assert result is False
        mock_redis.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_redis_connected_with_none():
    """Test Redis connection check with None client."""
    with patch("app.providers.redis.utils.logger") as mock_logger:
        result = await is_redis_connected(None)

        assert result is False
        mock_logger.error.assert_called_once()
        assert "Failed to connect to Redis" in mock_logger.error.call_args[0][0]
