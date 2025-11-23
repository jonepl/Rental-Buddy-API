from __future__ import annotations

from typing import Dict

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.domain.dto import ListingsRequest
from app.domain.range_types import Range
from app.providers.rentcast.mapper import build_params


def test_build_params_uses_lat_lon_with_radius(monkeypatch):
    req = ListingsRequest(
        latitude=30.0,
        longitude=-97.0,
        radius_miles=10,
        limit=25,
    )

    params = build_params(req)

    assert params["latitude"] == 30.0
    assert params["longitude"] == -97.0
    assert params["radius"] == 10
    assert params["limit"] == 25
    assert params["daysOld"] == settings.rentcast_days_old_default


def test_build_params_falls_back_to_address(monkeypatch):
    req = ListingsRequest(
        address="123 Main St",
        radius_miles=5,
        limit=10,
    )

    params = build_params(req)

    assert params["address"] == "123 Main St"


def test_build_params_falls_back_to_city_state(monkeypatch):
    req = ListingsRequest(
        city="Austin",
        state="TX",
        limit=10,
    )

    params = build_params(req)

    assert params["city"] == "Austin"
    assert params["state"] == "TX"


def test_build_params_falls_back_to_zip(monkeypatch):
    req = ListingsRequest(
        zip="78701",
        limit=10,
    )

    params = build_params(req)

    assert params["zipCode"] == "78701"


def test_build_params_applies_ranges(monkeypatch):
    req = ListingsRequest(
        latitude=30.0,
        longitude=-97.0,
        radius_miles=5,
        limit=10,
        beds=Range[int](min=2, max=4),
        baths=Range[float](min=1.5, max=3.5),
        price=Range[float](min=200000, max=400000),
        sqft=Range[int](min=1000, max=2000),
        year_built=Range[int](min=1990, max=2020),
        days_old=Range[int](min=1, max=30),
    )

    params = build_params(req)

    assert params["bedrooms"] == "2:4"
    assert params["bathrooms"] == "1.5:3.5"
    assert params["price"] == "200000:400000"
    assert params["squareFootage"] == "1000:2000"
    assert params["yearBuilt"] == "1990:2020"
    assert params["daysOld"] == "1:30"
