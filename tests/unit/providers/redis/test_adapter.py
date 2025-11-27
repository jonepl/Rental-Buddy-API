from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from redis.exceptions import RedisError

from app.providers.redis.adapter import RedisModelCacheAdapter


class TestModel(BaseModel):
    id: str
    name: str
    value: int


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def cache_adapter(mock_redis: AsyncMock) -> RedisModelCacheAdapter[TestModel]:
    return RedisModelCacheAdapter(
        redis=mock_redis, model_cls=TestModel, prefix="test", default_ttl=3600
    )


class TestRedisModelCacheAdapter:
    @pytest.mark.asyncio
    async def test_get_existing_key(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        test_data = '{"id": "1", "name": "test", "value": 42}'
        mock_redis.get.return_value = test_data.encode("utf-8")

        result = await cache_adapter.get("test_key")

        assert result is not None
        assert result.id == "1"
        assert result.name == "test"
        assert result.value == 42
        mock_redis.get.assert_awaited_once_with("test:test_key")

    @pytest.mark.asyncio
    async def test_get_missing_key(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        mock_redis.get.return_value = None

        result = await cache_adapter.get("missing_key")

        assert result is None
        mock_redis.get.assert_awaited_once_with("test:missing_key")

    @pytest.mark.asyncio
    async def test_get_deserialization_error(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        mock_redis.get.return_value = b"invalid json"

        result = await cache_adapter.get("invalid_key")

        assert result is None
        mock_redis.delete.assert_awaited_once_with("test:invalid_key")

    @pytest.mark.asyncio
    async def test_redis_error_handling(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        mock_redis.get.side_effect = RedisError("Connection error")

        result = await cache_adapter.get("error_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_value(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        test_model = TestModel(id="1", name="test", value=42)

        await cache_adapter.set("test_key", test_model)

        mock_redis.set.assert_awaited_once()
        args, kwargs = mock_redis.set.await_args
        assert args[0] == "test:test_key"
        assert '{"id":"1","name":"test","value":42}' in args[1]
        assert kwargs["ex"] == 3600  # Default TTL

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        test_model = TestModel(id="1", name="test", value=42)

        await cache_adapter.set("test_key", test_model, ttl_seconds=60)

        _, kwargs = mock_redis.set.await_args
        assert kwargs["ex"] == 60  # Custom TTL

    @pytest.mark.asyncio
    async def test_delete_key(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        await cache_adapter.delete("key_to_delete")

        mock_redis.delete.assert_awaited_once_with("test:key_to_delete")

    @pytest.mark.asyncio
    async def test_clear_all_keys(
        self, cache_adapter: RedisModelCacheAdapter[TestModel], mock_redis: AsyncMock
    ):
        mock_redis.scan.side_effect = [
            (1, [b"test:key1", b"test:key2"]),
            (0, []),  # Empty result to break the loop
        ]

        await cache_adapter.clear()

        mock_redis.scan.assert_called()
        mock_redis.delete.assert_awaited_once_with(b"test:key1", b"test:key2")

    @pytest.mark.asyncio
    async def test_custom_serializer_deserializer(self, mock_redis: AsyncMock):
        def custom_serializer(model: TestModel) -> str:
            return f"{model.id}:{model.name}"

        def custom_deserializer(data: str) -> TestModel:
            id, name = data.split(":")
            return TestModel(id=id, name=name, value=0)

        adapter = RedisModelCacheAdapter[TestModel](
            redis=mock_redis,
            model_cls=TestModel,
            prefix="custom",
            serializer=custom_serializer,
            deserializer=custom_deserializer,
        )

        # Test serialization
        test_model = TestModel(id="123", name="test", value=42)
        await adapter.set("custom_key", test_model)
        _, args, _ = mock_redis.set.mock_calls[0]
        assert args[1] == "123:test"

        # Test deserialization
        mock_redis.get.return_value = b"456:custom_test"
        result = await adapter.get("custom_key")
        assert result.id == "456"
        assert result.name == "custom_test"
        assert result.value == 0
