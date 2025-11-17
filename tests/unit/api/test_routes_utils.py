from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "service": "rental-buddy"}


def test_get_cache_stats():
    with patch(
        "app.api.routes_utils.cache_service.get_stats",
        return_value={"hits": 1, "misses": 2, "size": 3},
    ):
        resp = client.get("/api/v1/cache/stats")

        assert resp.status_code == 200
        assert resp.json() == {"hits": 1, "misses": 2, "size": 3}
