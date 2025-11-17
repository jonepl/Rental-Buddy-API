# app/domain/exceptions/provider_exceptions.py


class ProviderError(Exception):
    """Base class for all provider-related errors."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider does not respond before timeout."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider returns HTTP 429."""


class ProviderAuthError(ProviderError):
    """Raised when a provider returns 401 or 403."""


class ProviderClientError(ProviderError):
    """Raised for provider 4xx errors caused by bad requests (400, 402, etc.)"""


class ProviderServerError(ProviderError):
    """Raised for provider 5xx errors."""


class ProviderNetworkError(ProviderError):
    """Raised for network layer failures (DNS, SSL, connection abort)."""


class ProviderParsingError(ProviderError):
    """Raised when provider sends malformed, unexpected, or non-JSON payloads."""


class ProviderUnexpectedError(ProviderError):
    """Catch-all for any unexpected or unclassified provider failure."""
