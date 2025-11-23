from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.domain.enums.context_request import OperationType
from app.providers.enums.provider import Provider
from app.providers.opencage.client import OpenCageClient


@pytest.mark.asyncio
async def test_geocode_calls_http_get_json(monkeypatch):
    async_mock = AsyncMock(return_value={"results": []})
    monkeypatch.setattr(
        "app.providers.opencage.client.http_get_json",
        async_mock,
    )

    client = OpenCageClient(
        api_key="test-key",
        geocode_url="http://example.com",
        timeout_seconds=5,
    )

    params = {"q": "Austin"}
    result = await client.geocode(params)

    async_mock.assert_awaited_once_with(
        "http://example.com",
        {"q": "Austin", "key": "test-key"},
        {"accept": "application/json"},
        5,
        OperationType.GEOCODING,
        Provider.OPENCAGE,
        dict,
    )
    assert result == {"results": []}
