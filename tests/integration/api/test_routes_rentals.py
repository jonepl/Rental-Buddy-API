from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.deps import get_listings_service
from app.domain.exceptions.provider_exceptions import ProviderTimeoutError
from app.main import app
from tests.integration.api.helpers import StubListingsService

client = TestClient(app)


def override_listings_service(service: StubListingsService):
    app.dependency_overrides[get_listings_service] = lambda: service


def clear_overrides():
    app.dependency_overrides.pop(get_listings_service, None)


def test_rentals_success_returns_paginated_response(
    make_listing, stub_listings_service_factory
):
    listings = [
        make_listing("1", 2000, 3, 2.0, 1400, 30.001, -97.001, "A"),
        make_listing("2", 2500, 4, 3.0, 2000, 30.01, -97.01, "B"),
    ]
    service = stub_listings_service_factory(listings=listings)
    override_listings_service(service)

    try:
        resp = client.post(
            "/api/v1/rentals",
            json={
                "latitude": 30.0,
                "longitude": -97.0,
                "radius_miles": 5,
                "limit": 1,
                "offset": 0,
            },
        )
    finally:
        clear_overrides()

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["category"] == "rental"
    assert body["summary"]["page"]["limit"] == 1
    assert body["summary"]["page"]["next_offset"] == 1
    assert [l["id"] for l in body["listings"]] == ["1"]


def test_rentals_returns_provider_error_when_upstream_fails(
    stub_listings_service_factory,
):
    service = stub_listings_service_factory(error=ProviderTimeoutError("timeout"))
    override_listings_service(service)

    try:
        resp = client.post(
            "/api/v1/rentals",
            json={
                "latitude": 30.0,
                "longitude": -97.0,
                "radius_miles": 5,
            },
        )
    finally:
        clear_overrides()

    assert resp.status_code == 504
    body = resp.json()
    assert body["detail"]["error"] == "provider_timeout"
    assert body["detail"]["request_id"]
