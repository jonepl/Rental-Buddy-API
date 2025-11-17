import logging
from typing import Any, Dict, List

import httpx

from app.core.config import settings
from app.domain.enums.context_request import ContextRequest
from app.domain.exceptions.provider_exceptions import (
    ProviderAuthError,
    ProviderClientError,
    ProviderNetworkError,
    ProviderParsingError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderUnexpectedError,
)
from app.services.geocoding_service import GeocodingService

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
        return await self._get(self.sale_endpoint, params, ContextRequest.SALES)

    async def get_rentals(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return await self._get(self.rental_endpoint, params, ContextRequest.RENTALS)

    async def _get(
        self, url: str, params: Dict[str, Any], context: ContextRequest
    ) -> List[Dict[str, Any]]:
        headers = {"X-Api-Key": self.api_key, "accept": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("RentCast %s request: %s %s", context, url, params)
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

        except httpx.TimeoutException as e:
            logger.error("RentCast timeout (%s)", context)
            raise ProviderTimeoutError("RentCast timeout") from e

        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code == 429:
                raise ProviderRateLimitError("RentCast rate limit") from e
            if code in (401, 403):
                raise ProviderAuthError(f"RentCast auth error {code}") from e
            if code in (400, 402):
                raise ProviderClientError(f"RentCast client error {code}") from e
            if 500 <= code < 600:
                raise ProviderServerError(f"RentCast server error {code}") from e
            raise ProviderUnexpectedError(
                f"Unexpected RentCast HTTP error {code}"
            ) from e

        except httpx.HTTPError as e:
            raise ProviderNetworkError("RentCast network error") from e

        except Exception as e:
            raise ProviderUnexpectedError("RentCast unexpected error") from e

        try:
            payload = response.json()
        except ValueError as e:
            raise ProviderParsingError("Invalid JSON from RentCast") from e

        if not isinstance(payload, list):
            raise ProviderParsingError(
                f"Provider schema mismatch; expected list, got {type(payload).__name__}"
            )

        return payload
