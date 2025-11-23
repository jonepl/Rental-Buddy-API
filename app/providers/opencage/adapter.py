from app.domain.dto import Center, ListingsRequest
from app.domain.ports.geocoding_port import GeocodingPort
from app.providers.opencage.client import OpenCageClient
from app.providers.opencage.mapper import build_params
from app.providers.opencage.normalizer import normalize_response


class OpenCageAdapter(GeocodingPort):
    def __init__(self, client: OpenCageClient):
        self.client = client

    async def geocode(self, request: ListingsRequest) -> Center:
        """
        Geocode an address using the OpenCage Geocoding API.

        Args:
          request: The domain search request (filters, ranges, location, etc.).

        Returns:
          A Center object containing the geocoded latitude and longitude for the geocoded address, based on the following precedence:
            1. latitude + longitude (+ radius)
            2. address
            3. city + state
            4. zip.
        """
        params = build_params(request)
        response = await self.client.geocode(params)
        return normalize_response(response)
