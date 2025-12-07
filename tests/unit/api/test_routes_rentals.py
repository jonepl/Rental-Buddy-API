from __future__ import annotations

import sys
import types

if "redis" not in sys.modules:
    redis_module = types.ModuleType("redis")
    redis_async_module = types.ModuleType("redis.asyncio")

    class _DummyRedis:  # pragma: no cover - stub
        async def get(self, *_args, **_kwargs):
            return None

    class _DummyRedisError(Exception):
        pass

    redis_async_module.Redis = _DummyRedis
    redis_async_module.RedisError = _DummyRedisError
    redis_async_module.ConnectionError = _DummyRedisError
    redis_async_module.TimeoutError = _DummyRedisError
    redis_module.asyncio = redis_async_module
    sys.modules["redis"] = redis_module
    sys.modules["redis.asyncio"] = redis_async_module

from fastapi.testclient import TestClient

from app.api.deps import get_listings_service
from app.domain.dto import (ClusterRentStats, DistanceMetrics,
                            OverallRentMetrics, PropertyTypeStats,
                            RegionalMetrics)
from app.main import app


class DummyListingsService:
    def __init__(self, response: RegionalMetrics):
        self.response = response
        self.received_request = None

    async def get_regional_metrics(self, request):
        self.received_request = request
        return self.response


def test_regional_metrics_endpoint_returns_metrics():
    client = TestClient(app)
    metrics = RegionalMetrics(
        overall=OverallRentMetrics(count=0),
        distance=DistanceMetrics(),
        property_type_metrics=[
            PropertyTypeStats(
                property_type="single_family",
                count=0,
            )
        ],
        clusters_by_zip=[ClusterRentStats(cluster_key="unknown", count=0)],
    )
    dummy_service = DummyListingsService(metrics)

    async def override_service():
        return dummy_service

    app.dependency_overrides[get_listings_service] = override_service

    try:
        resp = client.post(
            "/api/v1/rentals/regional-metrics",
            json={"address": "123 Main St"},
        )

        assert resp.status_code == 200
        assert resp.json() == metrics.model_dump()
        assert dummy_service.received_request.address == "123 Main St"
    finally:
        app.dependency_overrides.pop(get_listings_service, None)
