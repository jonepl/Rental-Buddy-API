import logging

from app.core.config import settings
from app.domain.dto.listings import Center, ListingsRequest
from app.domain.ports.geocoding_port import GeocodingPort

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self, geocoding_port: GeocodingPort):
        self.geocoding_port = geocoding_port
        self.api_key = settings.opencage_api_key
        self.base_url = settings.opencage_url
        self.timeout = settings.request_timeout_seconds

    async def geocode(self, request: ListingsRequest) -> Center:
        """
        Geocode the provided search request using the configured port.
        """
        center: Center = await self.geocoding_port.geocode(request)
        return center
