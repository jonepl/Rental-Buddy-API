from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.domain.exceptions.provider_exceptions import (
    ProviderAuthError,
    ProviderClientError,
    ProviderParsingError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
)
from app.providers.rentcast.client import RentCastClient
from tests.unit.services.fixtures.rentcast_mocks import (
    MOCK_RENTCAST_RESPONSE,
    MOCK_RENTCAST_SALES_REQUEST,
)


class DummyResponse:
    def __init__(
        self, status_code=200, payload=None, json_exc=None, url="https://example.com"
    ):
        self.status_code = status_code
        self.payload = payload
        self.json_exc = json_exc
        self._request = httpx.Request("GET", url)

    def raise_for_status(self):
        if self.status_code >= 400:
            # Raise a real HTTPStatusError so the client’s except-blocks see it
            raise httpx.HTTPStatusError(
                message="error",
                request=self._request,
                response=httpx.Response(self.status_code, request=self._request),
            )

    def json(self):
        if self.json_exc:
            raise self.json_exc
        return self.payload


class TestRentCastClient:
    """Test the RentCastClient class"""

    @pytest.fixture
    def mock_settings(self):
        with patch("app.providers.rentcast.client.settings") as mock_settings:
            mock_settings.rentcast_api_key = "test_api_key"
            mock_settings.request_timeout_seconds = 12
            mock_settings.rentcast_sale_url = "test_sale_url"
            mock_settings.rentcast_rental_url = "test_rental_url"
            yield mock_settings

    @pytest.fixture
    def client(self):
        return RentCastClient()

    @pytest.fixture
    def mock_request(self):
        return MOCK_RENTCAST_SALES_REQUEST

    @pytest.fixture
    def mock_response(self):
        return DummyResponse(payload=MOCK_RENTCAST_RESPONSE)

    @pytest.mark.asyncio
    async def test_get_sales_success(
        self,
        client: RentCastClient,
        mock_request,
        mock_response: DummyResponse,
        mock_settings,
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings = await client.get_sales(mock_request)

            assert listings == mock_response.json()

    @pytest.mark.parametrize(
        "exception,expected_exception,status_code",
        [
            (httpx.TimeoutException("Request timed out"), ProviderTimeoutError, None),
            (
                httpx.HTTPStatusError(
                    "429", request=None, response=MagicMock(status_code=429)
                ),
                ProviderRateLimitError,
                429,
            ),
            (
                httpx.HTTPStatusError(
                    "401", request=None, response=MagicMock(status_code=401)
                ),
                ProviderAuthError,
                401,
            ),
            (
                httpx.HTTPStatusError(
                    "403", request=None, response=MagicMock(status_code=403)
                ),
                ProviderAuthError,
                403,
            ),
            (
                httpx.HTTPStatusError(
                    "400", request=None, response=MagicMock(status_code=400)
                ),
                ProviderClientError,
                400,
            ),
            (
                httpx.HTTPStatusError(
                    "402", request=None, response=MagicMock(status_code=402)
                ),
                ProviderClientError,
                402,
            ),
            (
                httpx.HTTPStatusError(
                    "500", request=None, response=MagicMock(status_code=500)
                ),
                ProviderServerError,
                500,
            ),
            (
                httpx.HTTPStatusError(
                    "502", request=None, response=MagicMock(status_code=502)
                ),
                ProviderServerError,
                502,
            ),
            (Exception("Unexpected"), Exception, None),
        ],
    )
    @pytest.mark.asyncio
    async def test_fetch_sales_error_handling(
        self,
        client: RentCastClient,
        mock_response,
        mock_settings,
        exception,
        expected_exception,
        status_code,
    ):
        """Test proper error propagation for all expected exception types"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response.status_code = status_code
            mock_client.get = AsyncMock(side_effect=exception)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with pytest.raises(expected_exception):
                await client.get_sales({})

    @pytest.mark.asyncio
    async def test_fetch_sales_invalid_json(
        self, client: RentCastClient, mock_response, mock_settings
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response.status_code = 200
            mock_response.json_exc = ValueError("Invalid JSON")
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ProviderParsingError):
                await client.get_sales({})

    @pytest.mark.asyncio
    async def test_get_rentals_success(
        self,
        client: RentCastClient,
        mock_request,
        mock_response: DummyResponse,
        mock_settings,
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings = await client.get_rentals(mock_request)

            assert listings == mock_response.json()

    @pytest.mark.parametrize(
        "exception,expected_exception,status_code",
        [
            (httpx.TimeoutException("Request timed out"), ProviderTimeoutError, None),
            (
                httpx.HTTPStatusError(
                    "429", request=None, response=MagicMock(status_code=429)
                ),
                ProviderRateLimitError,
                429,
            ),
            (
                httpx.HTTPStatusError(
                    "401", request=None, response=MagicMock(status_code=401)
                ),
                ProviderAuthError,
                401,
            ),
            (
                httpx.HTTPStatusError(
                    "403", request=None, response=MagicMock(status_code=403)
                ),
                ProviderAuthError,
                403,
            ),
            (
                httpx.HTTPStatusError(
                    "400", request=None, response=MagicMock(status_code=400)
                ),
                ProviderClientError,
                400,
            ),
            (
                httpx.HTTPStatusError(
                    "402", request=None, response=MagicMock(status_code=402)
                ),
                ProviderClientError,
                402,
            ),
            (
                httpx.HTTPStatusError(
                    "500", request=None, response=MagicMock(status_code=500)
                ),
                ProviderServerError,
                500,
            ),
            (
                httpx.HTTPStatusError(
                    "502", request=None, response=MagicMock(status_code=502)
                ),
                ProviderServerError,
                502,
            ),
            (Exception("Unexpected"), Exception, None),
        ],
    )
    @pytest.mark.asyncio
    async def test_fetch_rentals_error_handling(
        self,
        client: RentCastClient,
        mock_response,
        mock_settings,
        exception,
        expected_exception,
        status_code,
    ):
        """Test proper error propagation for all expected exception types"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response.status_code = status_code
            mock_client.get = AsyncMock(side_effect=exception)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with pytest.raises(expected_exception):
                await client.get_rentals({})

    @pytest.mark.asyncio
    async def test_fetch_rentals_invalid_json(
        self, client: RentCastClient, mock_response, mock_settings
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response.status_code = 200
            mock_response.json_exc = ValueError("Invalid JSON")
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ProviderParsingError):
                await client.get_rentals({})
