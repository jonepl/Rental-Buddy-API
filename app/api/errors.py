# app/api/errors.py
import logging

from fastapi import HTTPException, status

from app.domain.exceptions.provider_exceptions import (ProviderAuthError,
                                                       ProviderClientError,
                                                       ProviderError,
                                                       ProviderNetworkError,
                                                       ProviderParsingError,
                                                       ProviderRateLimitError,
                                                       ProviderServerError,
                                                       ProviderTimeoutError,
                                                       ProviderUnexpectedError)

logger = logging.getLogger(__name__)

# Exception type → (status_code, error_code, client_message)
PROVIDER_ERROR_MAP = {
    ProviderTimeoutError: (
        status.HTTP_504_GATEWAY_TIMEOUT,
        "provider_timeout",
        "Upstream service timed out. Please try again.",
    ),
    ProviderRateLimitError: (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "provider_rate_limited",
        "Upstream service is temporarily unavailable. Please retry later.",
    ),
    ProviderAuthError: (
        status.HTTP_401_UNAUTHORIZED,
        "provider_auth_error",
        "Authentication with upstream service failed.",
    ),
    ProviderClientError: (
        status.HTTP_400_BAD_REQUEST,
        "provider_client_error",
        "Invalid request was sent to the upstream service.",
    ),
    ProviderServerError: (
        status.HTTP_502_BAD_GATEWAY,
        "provider_server_error",
        "Upstream service encountered an error.",
    ),
    ProviderUnexpectedError: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "provider_unexpected",
        "An unexpected error occurred in the upstream service.",
    ),
    ProviderParsingError: (
        status.HTTP_502_BAD_GATEWAY,
        "provider_parsing_error",
        "Received an invalid response from the upstream service.",
    ),
    ProviderNetworkError: (
        status.HTTP_502_BAD_GATEWAY,
        "provider_network_error",
        "Network error while contacting the upstream service.",
    ),
}


def handle_provider_error(
    exc: ProviderError, operation: str, request_id: str
) -> HTTPException:
    """
    Convert provider exceptions into sanitized HTTPExceptions.
    """
    logger.warning(
        f"{operation}: {exc.error_code}",
        extra={"request_id": request_id},
        exc_info=True,
    )

    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.error_code,
            "message": exc.client_message,
            "request_id": request_id,
        },
    )
