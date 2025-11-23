from __future__ import annotations

import logging
from typing import Any, Dict

from app.core.config import settings
from app.domain.enums.context_request import OperationType
from app.providers.enums.provider import Provider
from app.providers.shared.http import http_get_json

logger = logging.getLogger(__name__)


class OpenCageClient:
    """
    Low-level HTTP client for OpenCage.

    Responsibilities:
      - HTTP transport, headers/params, timeout
      - error mapping to provider exceptions
      - JSON parsing

    It does NOT know about domain models; adapters map payloads to domain DTOs.
    """

    def __init__(
        self,
        api_key: str | None = None,
        geocode_url: str | None = None,
        timeout_seconds: int | float | None = None,
    ):
        self.api_key = api_key or settings.opencage_api_key
        self.geocode_url = geocode_url or settings.opencage_url
        self.timeout = timeout_seconds or settings.request_timeout_seconds

    async def geocode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a geocoding request against OpenCage.

        Args:
            params: Querystring parameters (without the API key; added automatically).
        """
        full_params = {**params, "key": self.api_key}
        headers = {"accept": "application/json"}
        return await http_get_json(
            self.geocode_url,
            full_params,
            headers,
            self.timeout,
            OperationType.GEOCODING,
            Provider.OPENCAGE,
            dict,
        )
