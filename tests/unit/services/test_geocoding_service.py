from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.domain.dto import Center, ListingsRequest
from app.domain.ports.geocoding_port import GeocodingPort
from app.services.geocoding_service import GeocodingService


@pytest.fixture
def geocoding_port() -> GeocodingPort:
    port = AsyncMock(spec=GeocodingPort)
    port.geocode = AsyncMock()
    return port


@pytest.fixture
def service(geocoding_port: GeocodingPort) -> GeocodingService:
    return GeocodingService(geocoding_port=geocoding_port)


@pytest.mark.asyncio
async def test_geocode_delegates_to_port(
    service: GeocodingService, geocoding_port: GeocodingPort
):
    request = ListingsRequest(latitude=30.0, longitude=-97.0, radius_miles=5.0, limit=1)
    expected = Center(lat=30.0, lon=-97.0)
    geocoding_port.geocode.return_value = expected

    result = await service.geocode(request)

    geocoding_port.geocode.assert_awaited_once_with(request)
    assert result == expected
