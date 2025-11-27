from unittest.mock import AsyncMock, patch

import pytest

from app.providers.redis.stats import _compute_hit_rate, get_redis_stats


class TestComputeHitRate:
    def test_with_hits_and_misses(self):
        """Test hit rate calculation with both hits and misses."""
        info = {"keyspace_hits": 75, "keyspace_misses": 25}
        assert _compute_hit_rate(info) == 0.75

    def test_with_zero_total(self):
        """Test hit rate calculation with no hits or misses."""
        info = {"keyspace_hits": 0, "keyspace_misses": 0}
        assert _compute_hit_rate(info) == 0.0

    def test_with_only_hits(self):
        """Test hit rate calculation with only hits."""
        info = {"keyspace_hits": 100, "keyspace_misses": 0}
        assert _compute_hit_rate(info) == 1.0

    def test_with_only_misses(self):
        """Test hit rate calculation with only misses."""
        info = {"keyspace_hits": 0, "keyspace_misses": 100}
        assert _compute_hit_rate(info) == 0.0


class TestGetRedisStats:
    @pytest.mark.asyncio
    async def test_successful_stats_retrieval(self):
        """Test successful retrieval of Redis statistics."""
        mock_redis = AsyncMock()
        mock_redis.info.side_effect = [
            {
                "keyspace_hits": 100,
                "keyspace_misses": 50,
                "evicted_keys": 10,
                "expired_keys": 5,
            },
            {"used_memory_human": "1.5M"},
        ]

        result = await get_redis_stats(mock_redis)

        assert result == {
            "hits": 100,
            "misses": 50,
            "hit_rate": 2 / 3,  # 100 / (100 + 50)
            "evicted_keys": 10,
            "expired_keys": 5,
            "used_memory_human": "1.5M",
        }

    @pytest.mark.asyncio
    async def test_redis_error_handling(self):
        """Test error handling when Redis commands fail."""
        mock_redis = AsyncMock()
        mock_redis.info.side_effect = Exception("Redis connection error")

        result = await get_redis_stats(mock_redis)

        assert "error" in result
        assert "Redis connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_stats_fields(self):
        """Test handling of missing fields in Redis stats."""
        mock_redis = AsyncMock()
        mock_redis.info.side_effect = [
            {},  # Empty stats
            {},  # Empty memory info
        ]

        result = await get_redis_stats(mock_redis)

        assert result == {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
            "evicted_keys": 0,
            "expired_keys": 0,
            "used_memory_human": None,
        }

    @pytest.mark.asyncio
    async def test_partial_stats_available(self):
        """Test handling when only some stats are available."""
        mock_redis = AsyncMock()
        mock_redis.info.side_effect = [
            {"keyspace_hits": 100},  # Only hits provided
            {"used_memory_human": "1.5M"},
        ]

        result = await get_redis_stats(mock_redis)

        assert result["hits"] == 100
        assert result["misses"] == 0  # Default value
        assert result["hit_rate"] == 1.0  # 100 / (100 + 0)
        assert result["used_memory_human"] == "1.5M"
