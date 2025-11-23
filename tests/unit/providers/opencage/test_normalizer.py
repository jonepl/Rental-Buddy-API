from __future__ import annotations

from app.domain.dto import Center
from app.providers.opencage.models import (Components, GeocodeResponse,
                                           Geometry, License, Rate, Result,
                                           Status, Timestamp)
from app.providers.opencage.normalizer import normalize_response


def make_response(lat: float, lon: float) -> GeocodeResponse:
    return GeocodeResponse(
        documentation="doc",
        licenses=[License(name="test", url="http://example.com")],
        rate=Rate(limit=1, remaining=1, reset=0),
        results=[
            Result(
                annotations=None,
                bounds=None,
                components=Components(),
                confidence=None,
                distance_from_q=None,
                formatted="formatted",
                geometry=Geometry(lat=lat, lng=lon),
            )
        ],
        status=Status(code=200, message="OK"),
        stay_informed=None,
        thanks=None,
        timestamp=Timestamp(created_http="now", created_unix=0),
        total_results=1,
    )


def test_normalize_response_returns_center():
    response = make_response(30.0, -97.0)

    center = normalize_response(response)

    assert isinstance(center, Center)
    assert center.lat == 30.0
    assert center.lon == -97.0
