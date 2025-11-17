from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from app.core.config import settings
from app.domain.dto import SearchRequest
from app.domain.range_types import Range


def build_rentcast_params(request: SearchRequest) -> dict:
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
        # You may or may not include radius here depending on API support
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

    # params = {
    #     "longitude": request.longitude,
    #     "latitude": request.latitude,
    #     "radius": request.radius_miles or settings.rentcast_radius_miles_default,
    #     "daysOld": request.days_old or settings.rentcast_days_old_default,
    #     "limit": min(50, settings.rentcast_request_cap),
    # }
    # # Map ranges directly to provider params
    # if request.beds is not None:
    #     params["bedrooms"] = request.beds.to_provider()
    # if request.baths is not None:
    #     params["bathrooms"] = request.baths.to_provider()
    # if request.days_old is not None:
    #     params["daysOld"] = request.days_old.to_provider()
    return params


def to_rentcast_params(
    req: SearchRequest,
    *,
    category: Literal["rental", "sale"],
    latitude: float,
    longitude: float,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": req.radius_miles,
    }

    # Scalars first
    if req.beds is not None:
        params["bedrooms"] = req.beds
    if req.baths is not None:
        params["bathrooms"] = req.baths
    if req.days_old is not None:
        params["daysOld"] = req.days_old

    # Ranges override scalars when provided
    beds_r = getattr(req, "beds_range", None)
    baths_r = getattr(req, "baths_range", None)
    price_r = getattr(req, "price_range", None)
    sqft_r = getattr(req, "sqft_range", None)
    year_r = getattr(req, "year_built_range", None)
    days_r = getattr(req, "days_old_range", None)

    if beds_r is not None:
        params["bedrooms"] = _range_to_str(beds_r)
    if baths_r is not None:
        params["bathrooms"] = _range_to_str(baths_r)
    if price_r is not None:
        params["price"] = _range_to_str(price_r)
    if sqft_r is not None:
        params["squareFootage"] = _range_to_str(sqft_r)
    if year_r is not None:
        params["yearBuilt"] = _range_to_str(year_r)
    if days_r is not None:
        params["daysOld"] = _range_to_str(days_r)

    # Category-specific
    if category == "sale" and getattr(req, "sale_date_range", None) is not None:
        params["saleDateRange"] = _range_to_str(getattr(req, "sale_date_range"))

    return {k: v for k, v in params.items() if v is not None}


def _range_to_str(r: Optional[Range]) -> Optional[str]:  # type: ignore[type-arg]
    if r is None:
        return None
    return r.to_provider()
