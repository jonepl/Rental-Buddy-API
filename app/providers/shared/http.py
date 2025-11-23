from __future__ import annotations

import logging
from typing import Any, Dict, Union
import httpx

from app.providers.enums.provider import Provider
from app.domain.enums.context_request import OperationType
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

logger = logging.getLogger(__name__)

async def http_get_json(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str] | None,
    timeout: float,
    operation: OperationType,
    provider: Provider,
    expected_type: type[dict] | type[list] = dict,
) -> Union[dict, list]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("%s %s request: %s %s", provider.value, operation.value, url, params)
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
    except httpx.TimeoutException as e:
        raise ProviderTimeoutError(f"{provider.value} timeout") from e
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 429:
            raise ProviderRateLimitError(f"{provider.value} rate limit") from e
        if code in (401, 403):
            raise ProviderAuthError(f"{provider.value} auth error {code}") from e
        if code in (400, 402):
            raise ProviderClientError(f"{provider.value} client error {code}") from e
        if 500 <= code < 600:
            raise ProviderServerError(f"{provider.value} server error {code}") from e
        raise ProviderUnexpectedError(f"Unexpected {provider.value} HTTP error {code}") from e
    except httpx.HTTPError as e:
        raise ProviderNetworkError(f"{provider.value} network error") from e
    except Exception as e:
        raise ProviderUnexpectedError(f"{provider.value} unexpected error") from e

    try:
        payload = response.json()
    except ValueError as e:
        raise ProviderParsingError(f"Invalid JSON from {provider.value}") from e

    if not isinstance(payload, expected_type):
        raise ProviderParsingError(
            f"Provider schema mismatch; expected {expected_type.__name__}, got {type(payload).__name__}"
        )
    return payload
