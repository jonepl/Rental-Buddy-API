from typing import Optional
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.domain.dto import (
    HOA,
    Address,
    Dates,
    Facts,
    NormalizedListing,
    Pricing,
    ProviderInfo,
)
from app.main import app
from tests.fixtures.request_data import FULL_REQUEST

client = TestClient(app)


def make_norm(
    id: str,
    price: Optional[float],
    beds: Optional[int],
    baths: Optional[float],
    sqft: Optional[int],
    lat: Optional[float],
    lon: Optional[float],
    formatted: Optional[str] = None,
):
    return NormalizedListing(
        id=id,
        category="sale",
        status="Active",
        address=Address(formatted=formatted, lat=lat, lon=lon),
        facts=Facts(beds=beds, baths=baths, sqft=sqft),
        pricing=Pricing(list_price=price),
        dates=Dates(),
        hoa=HOA(),
        provider=ProviderInfo(name="rentcast"),
    )


def test_sales_success_with_address_and_pagination():
    with patch(
        "app.api.routes_sales.GeocodingService.geocode_address",
        new=AsyncMock(return_value=(30.0, -97.0, "123 Main, Austin, TX")),
    ):
        listings = [
            make_norm("1", 300000, 3, 2.0, 1200, 30.001, -97.001, "A"),
            make_norm("2", 350000, 2, 1.5, 900, 30.01, -97.01, "B"),
        ]
        with patch(
            "app.api.routes_sales.PropertyService.get_sale_data",
            new=AsyncMock(return_value=[]),
        ):
            with patch(
                "app.api.routes_sales.normalize_rentcast_response",
                return_value=listings,
            ):
                # first page
                resp1 = client.post(
                    "/api/v1/sales",
                    json={
                        "address": "123 Main",
                        "radius_miles": 5,
                        "limit": 1,
                        "offset": 0,
                    },
                )
                assert resp1.status_code == 200
                body1 = resp1.json()
                assert body1["meta"]["category"] == "sale"
                assert body1["summary"]["page"]["limit"] == 1
                assert body1["summary"]["page"]["next_offset"] == 1
                assert len(body1["listings"]) == 1

                # second page
                resp2 = client.post(
                    "/api/v1/sales",
                    json={
                        "address": "123 Main",
                        "radius_miles": 5,
                        "limit": 1,
                        "offset": 1,
                    },
                )
                assert resp2.status_code == 200
                body2 = resp2.json()
                assert len(body2["listings"]) == 1


def test_sales_invalid_address_returns_400():
    with patch(
        "app.api.routes_sales.GeocodingService.geocode_address",
        new=AsyncMock(return_value=(None, None, "Could not resolve")),
    ):
        resp = client.post("/api/v1/sales", json={"address": "bad", "radius_miles": 5})
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data["detail"]


def test_sales_filters_and_sorting():
    listings = [
        make_norm("1", 280000, 3, 2.0, 1100, 30.001, -97.001, "A"),
        make_norm("2", 340000, 3, 2.0, 1500, 30.01, -97.01, "B"),
        make_norm("3", 360000, 3, 2.0, 1600, 30.02, -97.02, "C"),
    ]
    with patch(
        "app.api.routes_sales.PropertyService.get_sale_data",
        new=AsyncMock(return_value=[]),
    ):
        with patch(
            "app.api.routes_sales.normalize_rentcast_response", return_value=listings
        ):
            req = {
                "latitude": 30.0,
                "longitude": -97.0,
                "radius_miles": 5,
                "price": {"min": 300000},
                "sort": {"by": "price", "dir": "desc"},
            }
            resp = client.post("/api/v1/sales", json=req)
            assert resp.status_code == 200
            body = resp.json()
            prices = [item["pricing"]["list_price"] for item in body["listings"]]
            assert prices == sorted(prices, reverse=True)
            assert min(prices) >= 300000


def test_sales_lat_lon_missing_returns_400():
    resp = client.post("/api/v1/sales", json={"radius_miles": 5})
    assert resp.status_code in (400, 422)
