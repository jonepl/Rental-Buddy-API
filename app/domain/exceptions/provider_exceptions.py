# app/domain/exceptions/provider_exceptions.py


class ProviderError(Exception):
    """Base class for all provider-related errors."""

    status_code: int
    error_code: str
    client_message: str


class ProviderTimeoutError(ProviderError):
    """Raised when a provider does not respond before timeout."""

    status_code = 504
    error_code = "provider_timeout"
    client_message = "Upstream service timed out. Please try again."


class ProviderRateLimitError(ProviderError):
    """Raised when a provider returns HTTP 429."""

    status_code = 429
    error_code = "provider_rate_limited"
    client_message = "Upstream service is temporarily unavailable. Please retry later."


class ProviderAuthError(ProviderError):
    """Raised when a provider returns 401 or 403."""

    status_code = 401
    error_code = "provider_auth_error"
    client_message = "Authentication with upstream service failed."


class ProviderClientError(ProviderError):
    """Raised for provider 4xx errors caused by bad requests (400, 402, etc.)"""

    status_code = 400
    error_code = "provider_client_error"
    client_message = "Invalid request was sent to the upstream service."


class ProviderServerError(ProviderError):
    """Raised for provider 5xx errors."""

    status_code = 500
    error_code = "provider_server_error"
    client_message = "Upstream service encountered an error."


class ProviderNetworkError(ProviderError):
    """Raised for network layer failures (DNS, SSL, connection abort)."""

    status_code = 502
    error_code = "provider_network_error"
    client_message = "Network error while contacting the upstream service."


class ProviderParsingError(ProviderError):
    """Raised when provider sends malformed, unexpected, or non-JSON payloads."""

    status_code = 502
    error_code = "provider_parsing_error"
    client_message = "Received an invalid response from the upstream service."


class ProviderUnexpectedError(ProviderError):
    """Catch-all for any unexpected or unclassified provider failure."""

    status_code = 500
    error_code = "provider_unexpected"
    client_message = "An unexpected error occurred in the upstream service."
