from __future__ import annotations

import time
from typing import List

from app.api.presenters.listings_presenter import create_response
from app.domain.dto import (
    Address,
    Facts,
    ListingsRequest,
    NormalizedListing,
    Pricing,
    Range,
)
from app.domain.enums.context_request import OperationType


def _listing(listing_id: str, price: float) -> NormalizedListing:
    return NormalizedListing(
        id=listing_id,
        category="sale",
        status="Active",
        address=Address(formatted="123 Main"),
        facts=Facts(beds=3, baths=2.0, sqft=1500),
        pricing=Pricing(list_price=price),
    )


def test_create_response_maps_center_and_pagination():
    req = ListingsRequest(
        latitude=30.0,
        longitude=-97.0,
        radius_miles=5.0,
        limit=1,
        offset=0,
    )
    listings: List[NormalizedListing] = [_listing("1", 100), _listing("2", 200)]
    rid = "rid-123"
    start = time.perf_counter()

    result = create_response(listings, req, OperationType.SALES, rid, start)

    assert result.input.center.lat == 30.0
    assert result.input.center.lon == -97.0
    assert result.input.radius_miles == 5.0
    assert result.summary.returned == 1
    assert result.summary.page.next_offset == 1
    assert result.meta.category == "sale"
    assert result.meta.request_id == rid


def test_create_response_handles_optional_request_fields():
    req = ListingsRequest(
        address="123 Main St",
        radius_miles=10.0,
        beds=Range[int](min=2, max=4),
        baths=Range[float](min=1.5, max=2.5),
        days_old=Range[int](min=1, max=30),
        limit=10,
        offset=0,
    )
    listings = [_listing("1", 100)]
    start = time.perf_counter()

    result = create_response(listings, req, OperationType.RENTALS, "rid", start)

    assert result.input.location == "123 Main St"
    assert result.input.center is None  # no lat/lon supplied
    assert result.input.filters.beds == 2
    assert result.input.filters.baths == 1.5
    assert result.input.filters.days_old == "1"
    assert result.meta.category == "rental"
