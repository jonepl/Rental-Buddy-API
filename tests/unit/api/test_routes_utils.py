from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "service": "rental-buddy"}


def test_get_cache_stats():
    with patch("app.api.routes_utils.get_redis_stats") as mock_get_redis_stats:
        mock_get_redis_stats.return_value = {
            "hits": 1,
            "misses": 2,
            "hit_rate": 0.5,
            "evicted_keys": 0,
            "expired_keys": 0,
            "used_memory_human": "1.5M",
        }

        resp = client.get("/api/v1/cache/stats")

        assert resp.status_code == 200
        assert resp.json() == {
            "hits": 1,
            "misses": 2,
            "hit_rate": 0.5,
            "evicted_keys": 0,
            "expired_keys": 0,
            "used_memory_human": "1.5M",
        }
        mock_get_redis_stats.assert_called_once()
