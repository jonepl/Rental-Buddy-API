from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.providers.redis import client as redis_client


@pytest.fixture(autouse=True)
def reset_redis_client():
    """Reset the Redis client before each test."""
    redis_client._redis_client = None
    yield
    redis_client._redis_client = None


@pytest.mark.asyncio
@patch("app.providers.redis.client.Redis")
async def test_get_redis_client_initialization(mock_redis_class):
    """Test that get_redis_client initializes Redis client only once."""
    # First call - should initialize the client
    mock_redis_instance = AsyncMock()
    mock_redis_class.from_url.return_value = mock_redis_instance

    # Call the function twice
    client1 = await redis_client.get_redis_client()
    client2 = await redis_client.get_redis_client()

    # Verify Redis was initialized once with correct URL
    mock_redis_class.from_url.assert_called_once_with(
        settings.redis_url, decode_responses=False
    )

    # Verify the same instance is returned
    assert client1 is client2 is mock_redis_instance


@pytest.mark.asyncio
@patch("app.providers.redis.client.Redis")
async def test_close_redis_client(mock_redis_class):
    """Test that close_redis_client properly closes the connection."""
    # Setup
    mock_redis_instance = AsyncMock()
    mock_redis_class.from_url.return_value = mock_redis_instance

    # Get client to initialize it
    await redis_client.get_redis_client()

    # Close the client
    await redis_client.close_redis_client()

    # Verify close was called
    mock_redis_instance.close.assert_called_once()
    mock_redis_instance.wait_closed.assert_called_once()
    assert redis_client._redis_client is None


@pytest.mark.asyncio
@patch("app.providers.redis.client.Redis")
async def test_close_redis_client_when_none(mock_redis_class):
    """Test that close_redis_client handles case when client is None."""
    # Should not raise any exceptions
    await redis_client.close_redis_client()
    mock_redis_class.from_url.assert_not_called()


@pytest.mark.asyncio
@patch("app.providers.redis.client.Redis")
async def test_redis_client_reinitialization_after_close(mock_redis_class):
    """Test that client can be reinitialized after closing."""
    # First initialization
    mock_instance1 = AsyncMock()
    mock_redis_class.from_url.return_value = mock_instance1

    client1 = await redis_client.get_redis_client()
    await redis_client.close_redis_client()

    # Second initialization
    mock_instance2 = AsyncMock()
    mock_redis_class.from_url.return_value = mock_instance2
    mock_redis_class.from_url.reset_mock()

    client2 = await redis_client.get_redis_client()

    # Verify new instance was created
    mock_redis_class.from_url.assert_called_once()
    assert client1 is not client2
    assert client2 is mock_instance2
