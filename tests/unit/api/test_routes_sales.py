from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.deps import get_listings_service
from app.domain.dto.listings import (Address, Dates, Facts, NormalizedListing,
                                     Pricing)
from app.main import app


class StubListingsService:
    def __init__(self, sales):
        self.sales = sales
        self.last_request = None

    async def get_sale_data(self, request):
        self.last_request = request
        return self.sales


def _listing(listing_id: str, price: float, sqft: int) -> NormalizedListing:
    return NormalizedListing(
        id=listing_id,
        category="sale",
        address=Address(zip="99999", lat=31.0, lon=-98.0),
        facts=Facts(property_type="single_family", sqft=sqft, year_built=2000),
        pricing=Pricing(list_price=price),
        dates=Dates(listed="2024-01-01", last_seen="2024-01-05"),
    )


def test_sales_endpoint_includes_metrics():
    client = TestClient(app)
    sales = [_listing("s1", 350000, 1400), _listing("s2", 360000, 1500)]
    stub = StubListingsService(sales)

    async def override_service():
        return stub

    app.dependency_overrides[get_listings_service] = override_service
    try:
        resp = client.post(
            "/api/v1/sales",
            json={"latitude": 30.0, "longitude": -97.0, "radius_miles": 5.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["category"] == "sale"
        assert data["sales_metrics"]["overall"]["listing_count"] == 2
    finally:
        app.dependency_overrides.pop(get_listings_service, None)
