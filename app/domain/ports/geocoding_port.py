from typing import Protocol, runtime_checkable

from app.domain.dto import Center, ListingsRequest


@runtime_checkable
class GeocodingPort(Protocol):
    async def geocode(self, request: ListingsRequest) -> Center:
        """
        Geocode an address using the OpenCage Geocoding API.

        Args:
          request: The domain search request (filters, ranges, location, etc.).

        Returns:
          A tuple of (latitude, longitude) for the geocoded address, based on the following precedence:
            1. latitude + longitude (+ radius)
            2. address
            3. city + state
            4. zip.
        """
        ...
