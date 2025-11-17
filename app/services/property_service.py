import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.domain.dto import SearchRequest
from app.domain.ports.listings_port import ListingsPort
from app.domain.range_types import Range
from app.models.schemas import PropertyListing
from app.providers.rentcast.models import RentCastPropertyListing
from app.services.geocoding_service import GeocodingService
from app.utils.distance import haversine_distance

logger = logging.getLogger(__name__)


class PropertyService:
    def __init__(self, listings_port: ListingsPort):
        self.listings_port = listings_port

        # self.geocoder = geocoder
        # self.api_key = settings.rentcast_api_key
        # self.rental_endpoint = settings.rentcast_rental_url
        # self.sale_endpoint = settings.rentcast_sale_url
        # self.timeout = settings.request_timeout_seconds
        # self.request_cap = settings.rentcast_request_cap

    # async def get_rental_data(
    #     self,
    #     latitude: float,
    #     longitude: float,
    #     bedrooms: Optional[Range[int]] = None,
    #     bathrooms: Optional[Range[float]] = None,
    #     radius_miles: float = 5.0,
    #     days_old: Optional[Range[int]] = None,
    # ) -> List[PropertyListing]:
    #     """
    #     Fetch rental listings from RentCast API and return filtered/sorted comps

    #     Returns:
    #         List of PropertyListing objects, sorted by distance then price then sqft
    #     """
    #     params = {
    #         "latitude": latitude,
    #         "longitude": longitude,
    #         "radius": radius_miles or settings.rentcast_radius_miles_default,
    #         "daysOld": days_old or settings.rentcast_days_old_default,
    #         "limit": min(50, self.request_cap),
    #     }
    #     # Map ranges directly to provider params
    #     if bedrooms is not None:
    #         params["bedrooms"] = bedrooms.to_provider()
    #     if bathrooms is not None:
    #         params["bathrooms"] = bathrooms.to_provider()
    #     if days_old is not None:
    #         params["daysOld"] = days_old.to_provider()

    #     headers = {"X-Api-Key": self.api_key, "accept": "application/json"}

    #     try:
    #         async with httpx.AsyncClient(timeout=self.timeout) as client:
    #             logger.info(
    #                 f"Fetching rentals for {latitude}, {longitude}"
    #                 + (f" - {bedrooms}br" if bedrooms is not None else "")
    #                 + (f"/{bathrooms}ba" if bathrooms is not None else "")
    #             )
    #             response = await client.get(
    #                 self.rental_endpoint, params=params, headers=headers
    #             )
    #             response.raise_for_status()

    #             raw_listings = response.json()
    #             # listings = data.get("listings", [])

    #             # Process and filter listings
    #             listings = []
    #             seen_addresses = set()

    #             # derive local minimum thresholds from ranges for filtering
    #             target_min_bedrooms: Optional[int] = bedrooms.min if bedrooms is not None else None
    #             target_min_bathrooms: Optional[float] = bathrooms.min if bathrooms is not None else None

    #             for raw_listing in raw_listings:
    #                 comp = self._process_listing(
    #                     raw_listing, latitude, longitude, target_min_bedrooms, target_min_bathrooms
    #                 )
    #                 if comp and comp.address.lower() not in seen_addresses:
    #                     listings.append(comp)
    #                     seen_addresses.add(comp.address.lower())

    #             # Sort by distance, then price (asc), then sqft (desc)
    #             listings.sort(
    #                 key=lambda x: (x.distance_miles, x.price, -(x.square_footage or 0))
    #             )

    #             # Return up to configured max results
    #             return listings[: settings.max_results]

    #     except httpx.TimeoutException:
    #         logger.error("Timeout fetching rental data")
    #         return []
    #     except httpx.HTTPStatusError as e:
    #         if e.response.status_code == 429:
    #             logger.error("Rate limited by rental service")
    #             return []
    #         logger.error(f"HTTP error fetching rentals: {e}")
    #         return []
    #     except Exception as e:
    #         logger.error(f"Unexpected error fetching rentals: {e}")
    #         return []

    async def get_sale_data(
        self, request: SearchRequest
    ) -> Tuple[List[RentCastPropertyListing], float, float]:
        """
        Fetch sale listings from RentCast API and return filtered/sorted comps

        Returns:
            List of PropertyListing objects, sorted by distance then price then sqft
        """
        listings = await self.listings_port.fetch_sales(request)
        return listings[: settings.max_results]

    async def get_rental_data(
        self, request: SearchRequest
    ) -> Tuple[List[RentCastPropertyListing], float, float]:
        """
        Fetch rental listings from RentCast API and return filtered/sorted comps

        Returns:
            List of PropertyListing objects, sorted by distance then price then sqft
        """
        listings = await self.listings_port.fetch_rentals(request)
        return listings[: settings.max_results]

    async def get_mock_comps(
        self,
        request: SearchRequest,
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

    # async def _resolve_center(self, request: SearchRequest) -> Tuple[float, float]:
    #     if request.address:
    #         g_lat, g_lon, g_formatted = await self.geocoder.geocode_address(request.address)
    #         if g_lat is None or g_lon is None:
    #             raise HTTPException(status_code=400, detail={"error": {"code": "400_INVALID_INPUT", "message": g_formatted or "Could not resolve address", "details": {}}})
    #         lat, lon = g_lat, g_lon
    #     else:
    #         lat, lon = request.latitude, request.longitude
    #         if lat is None or lon is None:
    #             raise HTTPException(status_code=400, detail={"error": {"code": "400_INVALID_INPUT", "message": "Invalid location", "details": {}}})
    #     return lat, lon

    # # Deprecated
    # def _process_listing(
    #     self,
    #     listing: Dict[Any, Any],
    #     subject_lat: float,
    #     subject_lng: float,
    #     target_bedrooms: Optional[int],
    #     target_bathrooms: Optional[float],
    # ) -> Optional[PropertyListing]:
    #     """
    #     Process a single listing from RentCast API into a PropertyListing

    #     Returns None if listing should be filtered out
    #     """
    #     try:
    #         # Extract required fields
    #         address = listing.get("formattedAddress") or listing.get("address")
    #         city = listing.get("city")
    #         state = listing.get("state")
    #         state_fips = listing.get("stateFips")
    #         zip_code = listing.get("zipCode")
    #         county = listing.get("county")
    #         county_fips = listing.get("countyFips")
    #         latitude = listing.get("latitude")
    #         longitude = listing.get("longitude")
    #         property_type = listing.get("propertyType")
    #         year_built = listing.get("yearBuilt")
    #         status = listing.get("status")
    #         listing_type = listing.get("listingType")
    #         listed_date = listing.get("listedDate")
    #         removed_date = listing.get("removedDate")
    #         created_date = listing.get("createdDate")
    #         last_seen_date = listing.get("lastSeenDate")
    #         days_on_market = listing.get("daysOnMarket")
    #         mls_name = listing.get("mlsName")
    #         mls_number = listing.get("mlsNumber")
    #         listing_agent = listing.get("listingAgent")
    #         listing_office = listing.get("listingOffice")
    #         price = listing.get("price")
    #         bedrooms = listing.get("bedrooms")
    #         bathrooms = listing.get("bathrooms")
    #         square_footage = listing.get("squareFootage")

    #         # Filter out listings with missing critical data
    #         if not all([price, address, latitude, longitude]):
    #             return None

    #         # Ensure bed/bath minimums if provided. Guard against missing values in provider data.
    #         if target_bedrooms is not None and (
    #             bedrooms is None or bedrooms < target_bedrooms
    #         ):
    #             return None
    #         if target_bathrooms is not None and (
    #             bathrooms is None or bathrooms < target_bathrooms
    #         ):
    #             return None

    #         # Calculate distance
    #         distance = haversine_distance(subject_lat, subject_lng, latitude, longitude)

    #         return PropertyListing(
    #             address=address,
    #             city=city,
    #             state=state,
    #             zip_code=zip_code,
    #             county=county,
    #             latitude=latitude,
    #             longitude=longitude,
    #             price=int(price),
    #             bedrooms=int(bedrooms),
    #             bathrooms=float(bathrooms),
    #             square_footage=int(square_footage) if square_footage else None,
    #             distance_miles=distance,
    #         )

    #     except (ValueError, TypeError, KeyError) as e:
    #         logger.warning(f"Error processing listing: {e}")
    #         return None
