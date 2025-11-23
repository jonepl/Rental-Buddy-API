import logging
from typing import Any, Dict, List

from app.core.config import settings
from app.domain.enums.context_request import OperationType
from app.providers.enums.provider import Provider
from app.providers.shared.http import http_get_json

logger = logging.getLogger(__name__)


class RentCastClient:
    """
    Low-level HTTP client. Knows:
      - endpoints
      - headers
      - httpx
      - error mapping

    Does NOT know:
      - SearchRequest
      - domain models
    """

    def __init__(self):
        self.api_key = settings.rentcast_api_key
        self.timeout = settings.request_timeout_seconds
        self.sale_endpoint = settings.rentcast_sale_url
        self.rental_endpoint = settings.rentcast_rental_url

    async def get_sales(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        headers = {"X-Api-Key": self.api_key, "accept": "application/json"}
        return await http_get_json(
            self.sale_endpoint,
            params,
            headers,
            self.timeout,
            OperationType.SALES,
            Provider.RENTCAST,
            list,
        )

    async def get_rentals(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        headers = {"X-Api-Key": self.api_key, "accept": "application/json"}
        return await http_get_json(
            self.rental_endpoint,
            params,
            headers,
            self.timeout,
            OperationType.RENTALS,
            Provider.RENTCAST,
            list,
        )
