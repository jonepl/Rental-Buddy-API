from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.domain.dto import Range, SearchRequest
from app.domain.ports.listings_port import ListingsPort
from app.services.property_service import PropertyService
from tests.unit.services.fixtures.rentcast_mocks import (
    MOCK_RENTCAST_RESPONSE,
    MOCK_RENTCAST_SALES_REQUEST,
)


class TestPropertyService:
    """Test the PropertyService class"""

    @pytest.fixture
    def mock_listings_port(self):
        # Stub fetch_rentals and fetch_sales
        mock = AsyncMock(spec=ListingsPort)
        mock.fetch_rentals = AsyncMock(return_value=MOCK_RENTCAST_RESPONSE)
        mock.fetch_sales = AsyncMock(return_value=MOCK_RENTCAST_RESPONSE)
        return mock

    @pytest.fixture
    def mock_sale_request(self) -> SearchRequest:
        return MOCK_RENTCAST_SALES_REQUEST

    # @pytest.fixture
    # def mock_geocoder(self):
    #     # Create a mock geocoder
    #     mock = AsyncMock(spec=GeocodingService)
    #     # Configure the mock to return test coordinates
    #     mock.geocode_address.return_value = (30.2672, -97.7431, "123 Test St, Austin, TX")
    #     return mock

    @pytest.fixture
    def property_service(self, mock_listings_port):
        return PropertyService(listings_port=mock_listings_port)

    @pytest.fixture
    def mock_listing_response(self):
        return MOCK_RENTCAST_RESPONSE

    @pytest.fixture
    def mock_empty_response(self):
        return []

    @pytest.mark.asyncio
    async def test_get_sale_data_success(
        self,
        property_service: PropertyService,
        mock_listings_port,
        mock_sale_request,
        mock_listing_response,
    ):
        with patch.object(settings, "max_results", 2):
            mock_listings_port.fetch_sales.return_value = mock_listing_response

            listings = await property_service.get_sale_data(mock_sale_request)

            assert len(listings) == 2

    @pytest.mark.asyncio
    async def test_get_sale_data_no_results(
        self, property_service: PropertyService, mock_listings_port, mock_sale_request
    ):
        with patch.object(settings, "max_results", 2):
            mock_listings_port.fetch_sales.return_value = []

            listings = await property_service.get_sale_data(mock_sale_request)

            assert len(listings) == 0

    @pytest.mark.asyncio
    async def test_get_rental_data_success(
        self,
        property_service: PropertyService,
        mock_listings_port,
        mock_sale_request,
        mock_listing_response,
    ):
        with patch.object(settings, "max_results", 2):
            mock_listings_port.fetch_rentals.return_value = mock_listing_response

            listings = await property_service.get_rental_data(mock_sale_request)

            assert len(listings) == 2
