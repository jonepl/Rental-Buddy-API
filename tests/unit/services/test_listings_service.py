from __future__ import annotations

from typing import List
from unittest.mock import AsyncMock

import pytest

from app.domain.dto import (Address, CachedListings, Facts, ListingsRequest,
                            NormalizedListing, Pricing, SortSpec)
from app.domain.ports.listings_port import ListingsPort
from app.services.listings_service import ListingsService, sort_listings


def make_listing(
    list_price: float, beds: int, baths: float, sqft: int, listing_id: str
) -> NormalizedListing:
    return NormalizedListing(
        id=listing_id,
        category="sale",
        status="Active",
        address=Address(formatted="123 Main"),
        facts=Facts(beds=beds, baths=baths, sqft=sqft),
        pricing=Pricing(list_price=list_price),
    )


@pytest.fixture
def listings_port() -> ListingsPort:
    port = AsyncMock(spec=ListingsPort)
    port.fetch_sales = AsyncMock()
    port.fetch_rentals = AsyncMock()
    return port


@pytest.fixture
def cache_port():
    class CacheStub:
        def __init__(self):
            self.get = AsyncMock(return_value=None)
            self.set = AsyncMock()
            self.delete = AsyncMock()
            self.clear = AsyncMock()

    return CacheStub()


@pytest.fixture
def service(listings_port: ListingsPort, cache_port) -> ListingsService:
    return ListingsService(listings_port=listings_port, cache_port=cache_port)


@pytest.mark.asyncio
async def test_get_sale_data_sorts_by_requested_field(
    service: ListingsService, listings_port: ListingsPort, cache_port
):
    listings: List[NormalizedListing] = [
        make_listing(300000, 3, 2.0, 1400, "b"),
        make_listing(250000, 2, 1.5, 1000, "a"),
    ]
    listings_port.fetch_sales.return_value = listings
    req = ListingsRequest(latitude=1.0, longitude=1.0, radius_miles=5.0, limit=10)
    req.sort = SortSpec(by="price", dir="asc")

    result = await service.get_sale_data(req)

    listings_port.fetch_sales.assert_awaited_once_with(req)
    assert [l.id for l in result] == ["a", "b"]
    cache_port.get.assert_awaited_once()
    cache_port.set.assert_awaited_once()
    args, _ = cache_port.set.await_args
    assert isinstance(args[1], CachedListings)
    assert [l.id for l in args[1].items] == ["a", "b"]


@pytest.mark.asyncio
async def test_get_sale_data_returns_cached_items(
    service: ListingsService, listings_port: ListingsPort, cache_port
):
    cached_listings = [
        make_listing(400000, 4, 3.0, 2000, "cached"),
    ]
    cache_port.get.return_value = CachedListings(items=cached_listings)
    req = ListingsRequest(latitude=1.0, longitude=1.0, radius_miles=5.0, limit=10)

    result = await service.get_sale_data(req)

    assert result == cached_listings
    listings_port.fetch_sales.assert_not_awaited()
    cache_port.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_rental_data_caches_results(
    service: ListingsService, listings_port: ListingsPort, cache_port
):
    listings = [make_listing(1, 1, 1.0, 1, "a")]
    listings_port.fetch_rentals.return_value = listings
    req = ListingsRequest(latitude=1.0, longitude=1.0, radius_miles=5.0, limit=10)

    result = await service.get_rental_data(req)

    listings_port.fetch_rentals.assert_awaited_once_with(req)
    cache_port.get.assert_awaited_once()
    cache_port.set.assert_awaited_once()
    assert result == listings


@pytest.mark.asyncio
async def test_get_rental_data_returns_cached_items(
    service: ListingsService, listings_port: ListingsPort, cache_port
):
    cached_listings = [make_listing(1, 1, 1.0, 1, "cached-rental")]
    cache_port.get.return_value = CachedListings(items=cached_listings)
    req = ListingsRequest(latitude=1.0, longitude=1.0, radius_miles=5.0, limit=10)

    result = await service.get_rental_data(req)

    assert result == cached_listings
    listings_port.fetch_rentals.assert_not_awaited()
    cache_port.set.assert_not_awaited()


def test_sort_listings_handles_missing_sort_key():
    listings = [
        make_listing(100, 2, 2.0, 1200, "1"),
        make_listing(200, 3, 3.0, 1500, "2"),
    ]
    spec = SortSpec(by="distance", dir="asc")

    result = sort_listings(listings, spec)

    # unchanged order because distance not supported
    assert [l.id for l in result] == ["1", "2"]


@pytest.mark.asyncio
async def test_get_mock_comps_uses_request_defaults(service: ListingsService):
    req = ListingsRequest(
        latitude=30.0,
        longitude=-97.0,
        radius_miles=5.0,
        beds=None,
        baths=None,
    )

    comps = await service.get_mock_comps(req)

    assert len(comps) == 3
    assert comps[0].address.startswith("123 Mock St")
