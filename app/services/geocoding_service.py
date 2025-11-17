import logging
from typing import Optional, Tuple

import httpx

from app.core.config import settings
from app.models.schemas import ErrorCode

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self):
        self.api_key = settings.opencage_api_key
        self.base_url = settings.opencage_url
        self.timeout = settings.request_timeout_seconds

    async def geocode_address(
        self, address: str
    ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Geocode an address using OpenCage API

        Returns:
            Tuple of (latitude, longitude, formatted_address) or (None, None, error_message)
        """
        if not address or not address.strip():
            raise ValueError("Address cannot be empty")

        params = {
            "q": address.strip(),
            "key": self.api_key,
            "countrycode": "us",
            "limit": 1,
            "no_annotations": 1,
            "min_confidence": 9,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Geocoding address: {address}")
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

            except httpx.TimeoutException:
                logger.error(f"Timeout geocoding address: {address}")
                raise TimeoutError("Geocoding service timeout")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.error("Rate limited by geocoding service")
                    raise RuntimeError("Rate limited by geocoding service")

                if e.response.status_code in (400, 402):
                    logger.error("Invalid request to geocoding service")
                    raise ValueError("Invalid request to geocoding service")

                if e.response.status_code in (401, 403):
                    logger.error("Unauthorized request to geocoding service")
                    raise PermissionError("Unauthorized request to geocoding service")

                logger.error(f"Unexpected status code error: {e}")
                raise RuntimeError("Unexpected status code error")
            except httpx.HTTPError as e:
                logger.error(f"HTTP network error geocoding address: {e}")
                raise RuntimeError("HTTP network error geocoding address")
            except Exception as e:
                logger.error(f"Unexpected error geocoding address: {e}")
                raise RuntimeError("Unexpected error geocoding address")

            try:
                data: dict = response.json()

            except ValueError as e:
                logger.error(f"Invalid JSON from geocoding service: {e}")
                raise RuntimeError("Invalid JSON from geocoding service")

            results = data.get("results")
            if not results:
                logger.error(f"No results found for address: {address}")
                raise LookupError(f"No results found for address: {address}")

            result: dict = results[0]
            geometry: dict = result.get("geometry", {})

            latitude = geometry.get("lat")
            longitude = geometry.get("lng")
            formatted_address = result.get("formatted")

            if latitude is None or longitude is None:
                error_msg = "Geocoding service returned invalid coordinates"
                logger.error(f"{error_msg} for address: {address}")
                raise RuntimeError(error_msg)

            logger.info(f"Geocoded to: {latitude}, {longitude}")
            return float(longitude), float(latitude), formatted_address
