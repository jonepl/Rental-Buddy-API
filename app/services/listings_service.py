from __future__ import annotations

import json
import logging
from typing import List, Optional

from app.core.config import settings
from app.domain.dto.listings import (CachedListings, ListingsRequest,
                                     NormalizedListing, SortSpec)
from app.domain.dto.metrics import RentalMarketMetrics
from app.domain.enums.context_request import OperationType
from app.domain.listing_enrichment import enrich_listings
from app.domain.ports.caching_port import CachePort
from app.domain.ports.listings_port import ListingsPort
from app.domain.regional_metrics import compute_regional_metrics
from app.models.schemas import PropertyListing

logger = logging.getLogger(__name__)


class ListingsService:
    def __init__(
        self,
        listings_port: ListingsPort,
        cache_port: Optional[CachePort[CachedListings]] = None,
    ):
        self.listings_port = listings_port
        self.cache = cache_port

    async def get_sale_data(self, request: ListingsRequest) -> List[NormalizedListing]:
        """
        Fetch sale listings from RentCast API and return filtered/sorted comps

        Returns:
            List of PropertyListing objects, sorted by distance then price then sqft
        """
        cache_key = self._build_cache_key(request, OperationType.SALES)

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.info("Listings cache HIT (sales): %s", cache_key)
                return cached.items

        listings = await self.listings_port.fetch_sales(request)
        listings = sort_listings(listings, request.sort)
        enrich_listings(listings, request.latitude, request.longitude)

        if self.cache:
            await self.cache.set(cache_key, CachedListings(items=listings))
            logger.info("Listings cache SET (sales): %s", cache_key)

        return listings

    async def get_rental_data(
        self, request: ListingsRequest
    ) -> List[NormalizedListing]:
        """
        Fetch rental listings from RentCast API and return filtered/sorted comps

        Returns:
            List of PropertyListing objects, sorted by distance then price then sqft
        """
        cache_key = self._build_cache_key(request, OperationType.RENTALS)

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.info("Listings cache HIT (rentals): %s", cache_key)
                return cached.items

        listings = await self.listings_port.fetch_rentals(request)
        listings = sort_listings(listings, request.sort)
        enrich_listings(listings, request.latitude, request.longitude)

        if self.cache:
            await self.cache.set(cache_key, CachedListings(items=listings))
            logger.info("Listings cache SET (rentals): %s", cache_key)

        return listings

    async def get_regional_metrics(self, request: ListingsRequest) -> RentalMarketMetrics:
        rentals = await self.get_rental_data(request)
        center_lat = request.latitude
        center_lon = request.longitude
        return compute_regional_metrics(rentals, center_lat, center_lon)

    async def get_mock_comps(
        self,
        request: ListingsRequest,
    ) -> List[PropertyListing]:
        """
        Return mock rental comps for testing when real API is unavailable
        """
        mock_listings = [
            {
                "address": f"123 Mock St, Test City, FL 33301",
                "city": "Test City",
                "state": "FL",
                "zip_code": "33301",
                "county": "Test County",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "price": 2400,
                "bedrooms": request.beds.min if request.beds is not None else 2,
                "bathrooms": request.baths.min if request.baths is not None else 1.5,
                "square_footage": 1400,
                "distance_miles": 0.8,
            },
            {
                "address": f"456 Sample Ave, Test City, FL 33301",
                "city": "Test City",
                "state": "FL",
                "zip_code": "33301",
                "county": "Test County",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "price": 2300,
                "bedrooms": request.beds.min if request.beds is not None else 3,
                "bathrooms": request.baths.min if request.baths is not None else 2.0,
                "square_footage": 1350,
                "distance_miles": 1.2,
            },
            {
                "address": f"789 Demo Blvd, Test City, FL 33301",
                "city": "Test City",
                "state": "FL",
                "zip_code": "33301",
                "county": "Test County",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "price": 2500,
                "bedrooms": request.beds.min if request.beds is not None else 1,
                "bathrooms": request.baths.min if request.baths is not None else 1.0,
                "square_footage": 1500,
                "distance_miles": 1.5,
            },
        ]

        return [PropertyListing(**listing) for listing in mock_listings]

    def _build_cache_key(
        self,
        request: ListingsRequest,
        op: OperationType,
    ) -> str:
        """
        Build a stable cache key from the request.
        """
        payload = json.dumps(request.model_dump(), sort_keys=True)
        return f"{op.value}:{payload}"


def sort_listings(
    listings: List[NormalizedListing], sort: SortSpec
) -> List[NormalizedListing]:
    reverse = sort.dir == "desc"
    key_builders = {
        "price": lambda x: (x.pricing.list_price is None, x.pricing.list_price or 0),
        "beds": lambda x: (x.facts.beds is None, x.facts.beds or 0),
        "baths": lambda x: (x.facts.baths is None, x.facts.baths or 0),
        "sqft": lambda x: (x.facts.sqft is None, x.facts.sqft or 0),
    }
    key_fn = key_builders.get(sort.by)
    if key_fn:
        listings = sorted(listings, key=key_fn, reverse=reverse)
    return listings
