from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.models.schemas import PropertyListing
from app.services.property_service import PropertyService
from tests.unit.services.test_data.property_service_mock import \
    MOCK_RENTCAST_RESPONSE


class TestRentalService:
    """Test the PropertyService class"""

    @pytest.fixture
    def property_service(self):
        return PropertyService()

    @pytest.fixture
    def mock_rental_response(self):
        return MOCK_RENTCAST_RESPONSE

    @pytest.fixture
    def mock_empty_response(self):
        return []

    @pytest.mark.asyncio
    async def test_get_rental_data_success(
        self, property_service: PropertyService, mock_rental_response
    ):
        """Test successful retrieval of rental comps"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_rental_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            comps = await property_service.get_rental_data(
                latitude=30.2672, longitude=-97.7431, bedrooms=1, bathrooms=1.5
            )

            args, _ = mock_client.get.await_args
            assert args[0] == settings.rentcast_rental_url
            assert len(comps) == 2
            assert isinstance(comps[0], PropertyListing)
            assert comps[0].address == "456 Oak Ave, Austin, TX 78702"
            assert comps[0].price == 2450
            assert comps[0].bedrooms == 2
            assert comps[0].bathrooms == 2.0
            assert comps[0].square_footage == 1025
            assert comps[0].distance_miles == 1.4

    @pytest.mark.asyncio
    async def test_get_rental_data_no_results(
        self, property_service: PropertyService, mock_empty_response
    ):
        """Test when no rental comps are found"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_empty_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            comps = await property_service.get_rental_data(
                latitude=30.2672, longitude=-97.7431, bedrooms=2, bathrooms=1.5
            )

            assert len(comps) == 0

    @pytest.mark.asyncio
    async def test_get_rental_data_http_error(self, property_service: PropertyService):
        """Test handling of HTTP errors from the API"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
            )
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            comps = await property_service.get_rental_data(
                latitude=30.2672, longitude=-97.7431, bedrooms=2, bathrooms=1.5
            )

            # On HTTP errors, service returns an empty list
            assert comps == []

    @pytest.mark.asyncio
    async def test_get_rental_data_timeout(self, property_service: PropertyService):
        """Test handling of timeout errors"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            comps = await property_service.get_rental_data(
                latitude=30.2672, longitude=-97.7431, bedrooms=2, bathrooms=1.5
            )

            # On timeout, service returns an empty list
            assert comps == []

    @pytest.mark.asyncio
    async def test_get_rental_data_invalid_response(
        self, property_service: PropertyService
    ):
        """Test handling of invalid API response"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"invalid": "response"}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            comps = await property_service.get_rental_data(
                latitude=30.2672, longitude=-97.7431, bedrooms=2, bathrooms=1.5
            )

            # Invalid response should be handled gracefully with empty list
            assert comps == []

    @pytest.mark.asyncio
    async def test_get_rental_data_sorts_by_distance_then_price(
        self, property_service: PropertyService, mock_rental_response
    ):
        """Test that comps are sorted by distance then price"""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_rental_response
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            comps = await property_service.get_rental_data(
                latitude=30.2672, longitude=-97.7431, bedrooms=2, bathrooms=1.5
            )

            assert len(comps) == 2
            # First comp should be the one at the exact same coordinates
            assert comps[0].address == "456 Oak Ave, Austin, TX 78702"
            # Second comp should be the further one
            assert comps[1].address == "123 Main St, Austin, TX 78701"
