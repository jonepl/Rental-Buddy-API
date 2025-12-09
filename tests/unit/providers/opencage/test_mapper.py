from __future__ import annotations

from app.domain.dto.listings import ListingsRequest
from app.providers.opencage.mapper import build_params


def test_build_params_with_lat_lon():
    req = ListingsRequest(latitude=30.0, longitude=-97.0, radius_miles=7.5, limit=10)

    params = build_params(req)

    assert params["q"] == "30.0%2C-97.0"
    assert params["radius_miles"] == "7.5"


def test_build_params_with_address():
    req = ListingsRequest(address=" 123 Main St ", limit=5)

    params = build_params(req)

    assert params["q"] == "123%20Main%20St"


def test_build_params_with_city_state():
    req = ListingsRequest.model_construct(city="Austin", state="TX")

    params = build_params(req)

    assert params["q"] == "Austin%2C%20TX"


def test_build_params_with_zip():
    req = ListingsRequest.model_construct(zip="78701")

    params = build_params(req)

    assert params["q"] == "78701%2C%20USA"


def test_build_params_when_missing_location():
    req = ListingsRequest.model_construct()

    params = build_params(req)

    assert params["q"] == ""
