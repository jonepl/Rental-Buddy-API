from __future__ import annotations

from typing import Any, Dict

from app.core.config import settings
from app.domain.dto import ListingsRequest


def build_params(request: ListingsRequest) -> dict:
    """
    Map a domain-level SearchRequest to RentCast query params.

    Location precedence:
      1. latitude + longitude (+ radius)
      2. address
      3. city + state
      4. zip

    Raises:
      ValueError if no usable location is provided.
    """
    params: Dict[str, Any] = {}

    # --- 1. Location strategy ---
    if request.latitude is not None and request.longitude is not None:
        params["latitude"] = request.latitude
        params["longitude"] = request.longitude
        params["radius"] = (
            request.radius_miles or settings.rentcast_radius_miles_default
        )
    elif request.address:
        params["address"] = request.address
        params["radius"] = (
            request.radius_miles or settings.rentcast_radius_miles_default
        )
    elif request.city and request.state:
        params["city"] = request.city
        params["state"] = request.state
    elif request.zip:
        params["zipCode"] = request.zip
    else:
        raise ValueError(
            "SearchRequest must include either lat/lon, address, city+state, or zip"
        )

    # --- 2. Ranges / filters ---
    if request.beds is not None:
        params["bedrooms"] = request.beds.to_provider()
    if request.baths is not None:
        params["bathrooms"] = request.baths.to_provider()
    if request.price is not None:
        params["price"] = request.price.to_provider()
    if request.sqft is not None:
        params["squareFootage"] = request.sqft.to_provider()
    if request.year_built is not None:
        params["yearBuilt"] = request.year_built.to_provider()
    if request.days_old is not None:
        params["daysOld"] = request.days_old.to_provider()
    else:
        # default days_old if not explicitly provided
        params["daysOld"] = settings.rentcast_days_old_default

    # --- 3. Limit (offset RentCast may or may not support directly) ---
    params["limit"] = min(request.limit, settings.rentcast_request_cap, 100)

    return params
