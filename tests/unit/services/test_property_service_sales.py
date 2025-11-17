from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.domain.dto import Range, SearchRequest
from app.providers.rentcast.models import RentCastPropertyListing
from app.services.geocoding_service import GeocodingService
from app.services.property_service import PropertyService
from tests.unit.services.fixtures.rentcast_mocks import (
    MOCK_RENTCAST_SALES_REQUEST,
    MOCK_RENTCAST_SALES_RESPONSE,
)


class TestPropertyServiceSales:
    @pytest.fixture
    def mock_geocoder(self):
        # Create a mock geocoder
        mock = AsyncMock(spec=GeocodingService)
        # Configure the mock to return test coordinates
        mock.geocode_address.return_value = (
            MOCK_RENTCAST_SALES_REQUEST.latitude,
            MOCK_RENTCAST_SALES_REQUEST.longitude,
            "123 Test St, Austin, TX",
        )
        return mock

    @pytest.fixture
    def property_service(self, mock_geocoder):
        return PropertyService(geocoder=mock_geocoder)

    @pytest.fixture
    def mock_sale_request(self) -> SearchRequest:
        return MOCK_RENTCAST_SALES_REQUEST

    @pytest.fixture
    def mock_sale_response(self) -> List[RentCastPropertyListing]:
        # Reuse rental-shaped mock for sale; processing is identical
        return MOCK_RENTCAST_SALES_RESPONSE

    @pytest.fixture
    def mock_empty_response(self):
        return []

    @pytest.mark.asyncio
    async def test_get_sale_data_success(
        self, property_service: PropertyService, mock_sale_request, mock_sale_response
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_sale_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings, lng, lat = await property_service.get_sale_data(mock_sale_request)

            args, call_kwargs = mock_client.get.await_args
            assert args[0] == settings.rentcast_sale_url
            assert call_kwargs["params"]["latitude"] == mock_sale_request.latitude
            assert call_kwargs["params"]["longitude"] == mock_sale_request.longitude
            assert call_kwargs["params"]["radius"] == 10.0
            assert call_kwargs["params"]["limit"] == 50
            assert call_kwargs["params"]["bedrooms"] == "1:3"
            assert call_kwargs["params"]["bathrooms"] == "1.5:*"
            assert call_kwargs["params"]["daysOld"] == "*:30"

            # Basic output checks
            assert isinstance(listings, list)
            assert isinstance(lat, float)
            assert isinstance(lng, float)
            assert len(listings) == 5
            assert listings[0].get("formattedAddress")
            assert listings[0].get("price") > 0
            assert lat == mock_sale_request.latitude
            assert lng == mock_sale_request.longitude

    @pytest.mark.asyncio
    async def test_get_sale_data_no_results(
        self, property_service: PropertyService, mock_empty_response, mock_sale_request
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_empty_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings, lng, lat = await property_service.get_sale_data(mock_sale_request)
            assert listings == []
            assert isinstance(lat, float)
            assert isinstance(lng, float)

    @pytest.mark.asyncio
    async def test_get_sale_data_http_error(
        self, property_service: PropertyService, mock_sale_request
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            # Simulate raise_for_status raising HTTPStatusError
            request = httpx.Request("GET", settings.rentcast_sale_url)
            response = httpx.Response(500, request=request)
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=request, response=response
            )
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings, lng, lat = await property_service.get_sale_data(mock_sale_request)
            assert listings == []
            assert lat is None
            assert lng is None

    @pytest.mark.asyncio
    async def test_get_sale_data_timeout(
        self, property_service: PropertyService, mock_sale_request
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings, lng, lat = await property_service.get_sale_data(mock_sale_request)
            assert listings == []
            assert lat is None
            assert lng is None

    @pytest.mark.asyncio
    async def test_get_sale_data_invalid_response(
        self, property_service: PropertyService, mock_sale_request
    ):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            # Return a dict to break iteration/processing
            mock_response.json.return_value = {"unexpected": True}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            listings, lng, lat = await property_service.get_sale_data(mock_sale_request)
            assert listings == []
            assert lat is None
            assert lng is None
