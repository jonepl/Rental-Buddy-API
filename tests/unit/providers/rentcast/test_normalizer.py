from __future__ import annotations

from typing import Dict, List

from app.providers.rentcast.normalizer import (normalize_listing,
                                               normalize_response)


def test_normalize_rentcast_listing_rental():
    raw = {
        "id": "123",
        "formattedAddress": "123 Main St",
        "city": "Austin",
        "state": "TX",
        "zip": "78701",
        "county": "Travis",
        "latitude": 30.0,
        "longitude": -97.0,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "squareFootage": 1500,
        "price": 2500,
        "listed": "2024-01-01",
        "status": "Active",
        "hoaFee": 150,
    }

    listing = normalize_listing(raw, "rental")

    assert listing.id == "prov:rentcast:123"
    assert listing.category == "rental"
    assert listing.address.formatted == "123 Main St"
    assert listing.address.city == "Austin"
    assert listing.facts.beds == 3
    assert listing.pricing.list_price == 2500
    assert listing.pricing.period == "monthly"
    assert listing.dates.listed == "2024-01-01"
    assert listing.hoa.monthly == 150


def test_normalize_rentcast_listing_sale_fallbacks():
    raw = {
        "listing_id": "456",
        "address": "456 Elm",
        "line1": "456 Elm",
        "line2": "Unit 2",
        "city": "Austin",
        "state": "TX",
        "zip": "78702",
        "lat": 30.1,
        "lon": -97.1,
        "bedrooms": 4,
        "bathrooms": 3.0,
        "sqft": 2000,
        "price": 550000,
        "status": "Sold",
        "last_seen": "2024-01-02",
    }

    listing = normalize_listing(raw, "sale")

    assert listing.id == "prov:rentcast:456"
    assert listing.category == "sale"
    assert listing.address.line2 == "Unit 2"
    assert listing.facts.sqft == 2000
    assert listing.pricing.period == "total"
    assert listing.dates.last_seen == "2024-01-02"
    assert listing.hoa.monthly == 0


def test_normalize_rentcast_response_batch():
    raw_rows: List[Dict[str, object]] = [
        {"id": "1", "price": 100},
        {"id": "2", "price": 200},
    ]

    listings = normalize_response(raw_rows, "rental")

    assert len(listings) == 2
    assert [listing.id for listing in listings] == [
        "prov:rentcast:1",
        "prov:rentcast:2",
    ]
