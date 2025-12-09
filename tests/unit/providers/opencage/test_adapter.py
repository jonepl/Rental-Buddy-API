from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.domain.dto.listings import Center, ListingsRequest
from app.providers.opencage.adapter import OpenCageAdapter


# TODO: refactor to use fixture
@pytest.mark.asyncio
async def test_adapter_geocode(monkeypatch):
    req = ListingsRequest(address="123 Main St", limit=5)

    captured = {}

    def fake_build_params(request):
        captured["request"] = request
        return {"q": "123"}

    monkeypatch.setattr(
        "app.providers.opencage.adapter.build_params",
        fake_build_params,
    )
    monkeypatch.setattr(
        "app.providers.opencage.adapter.normalize_response",
        lambda resp: Center(lat=1.0, lon=-2.0),
    )

    mock_client = AsyncMock()
    mock_client.geocode.return_value = {"raw": "data"}

    adapter = OpenCageAdapter(mock_client)

    center = await adapter.geocode(req)

    assert captured["request"] is req
    mock_client.geocode.assert_awaited_once_with({"q": "123"})
    assert center.lat == 1.0
    assert center.lon == -2.0
