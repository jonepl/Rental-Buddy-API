from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.dto import ListingsRequest, Range
from app.domain.enums.context_request import OperationType
from app.providers.rentcast.adapter import RentCastAdapter
from app.providers.rentcast.client import RentCastClient


class TestRentCastAdapter:
    """Test the RentCastAdapter class"""

    @pytest.fixture
    def mock_rentcast_client(self):
        return AsyncMock(spec=RentCastClient)

    @pytest.fixture
    def adapter(self, mock_rentcast_client):
        return RentCastAdapter(mock_rentcast_client)

    @pytest.fixture
    def sample_request(self):
        return ListingsRequest(
            address="123 Test St, Austin, TX",
            beds=Range(min=2, max=3),
            baths=Range(min=2.0),
            price=Range(max=500000),
            sqft=Range(min=1000),
            days_old=Range(max=30),
            radius_miles=10.0,
        )

    @pytest.fixture
    def mock_build_params(self):
        with patch("app.providers.rentcast.adapter.build_params") as mock:
            mock.return_value = {}
            yield mock

    @pytest.fixture
    def mock_normalize_response(self):
        with patch("app.providers.rentcast.adapter.normalize_response") as mock:
            mock.return_value = []
            yield mock

    @pytest.mark.asyncio
    async def test_fetch_sales_success(
        self,
        adapter: RentCastAdapter,
        sample_request: ListingsRequest,
        mock_build_params,
        mock_normalize_response,
    ):
        """Test successful fetch of sales listings"""
        mock_response = [
            {"id": "1", "price": 300000, "bedrooms": 2, "bathrooms": 2.0},
            {"id": "2", "price": 400000, "bedrooms": 3, "bathrooms": 2.5},
        ]
        adapter.client.get_sales.return_value = mock_response
        mock_normalize_response.return_value = mock_response

        result = await adapter.fetch_sales(sample_request)

        assert len(result) == 2
        mock_build_params.assert_called_once_with(sample_request)
        adapter.client.get_sales.assert_called_once_with(mock_build_params.return_value)
        mock_normalize_response.assert_called_once_with(
            mock_response, OperationType.SALES
        )

    @pytest.mark.asyncio
    async def test_fetch_sales_empty_response(
        self,
        adapter: RentCastAdapter,
        sample_request: ListingsRequest,
        mock_build_params,
        mock_normalize_response,
    ):
        """Test handling of empty response"""
        adapter.client.get_sales.return_value = []

        result = await adapter.fetch_sales(sample_request)

        assert result == []
        mock_build_params.assert_called_once_with(sample_request)
        adapter.client.get_sales.assert_called_once_with(mock_build_params.return_value)
        mock_normalize_response.assert_called_once_with([], OperationType.SALES)

    @pytest.mark.asyncio
    async def test_fetch_rentals_success(
        self,
        adapter: RentCastAdapter,
        sample_request: ListingsRequest,
        mock_build_params,
        mock_normalize_response,
    ):
        """Test successful fetch of rental listings"""
        mock_response = [
            {"id": "1", "price": 300000, "bedrooms": 2, "bathrooms": 2.0},
            {"id": "2", "price": 400000, "bedrooms": 3, "bathrooms": 2.5},
        ]
        adapter.client.get_rentals.return_value = mock_response
        mock_normalize_response.return_value = mock_response

        result = await adapter.fetch_rentals(sample_request)

        assert len(result) == 2
        mock_build_params.assert_called_once_with(sample_request)
        adapter.client.get_rentals.assert_called_once_with(
            mock_build_params.return_value
        )
        mock_normalize_response.assert_called_once_with(
            mock_response, OperationType.RENTALS
        )

    @pytest.mark.asyncio
    async def test_fetch_rentals_empty_response(
        self,
        adapter: RentCastAdapter,
        sample_request: ListingsRequest,
        mock_build_params,
        mock_normalize_response,
    ):
        """Test handling of empty response"""
        adapter.client.get_rentals.return_value = []

        result = await adapter.fetch_rentals(sample_request)

        assert result == []
        mock_build_params.assert_called_once_with(sample_request)
        adapter.client.get_rentals.assert_called_once_with(
            mock_build_params.return_value
        )
        mock_normalize_response.assert_called_once_with([], OperationType.RENTALS)
