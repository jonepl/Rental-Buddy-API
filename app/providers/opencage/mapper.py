from typing import Dict
from urllib.parse import quote

from app.domain.dto.listings import ListingsRequest  # adjust import as needed


def build_params(req: ListingsRequest) -> Dict[str, str]:
    """
    Build OpenCage API parameters based on ListingsRequest.
    Field precedence:

        1. latitude + longitude (+ radius)
        2. address
        3. city + state
        4. zip

    Returns: dict suitable for `params` in requests.get(...)
    """

    params: Dict[str, str] = {}

    # ----------------------------------------
    # 1. Latitude + Longitude (+ optional radius)
    # ----------------------------------------
    if req.latitude is not None and req.longitude is not None:
        params["q"] = quote(f"{req.latitude},{req.longitude}")
        # OpenCage radius must be in meters (if you use "bounds" or "proximity")
        # but here we just include it as a custom field unless you want bounds calc.
        params["radius_miles"] = str(req.radius_miles)
        return params

    # ----------------------------------------
    # 2. Address only
    # ----------------------------------------
    if req.address:
        cleaned = req.address.strip()
        if cleaned:
            params["q"] = quote(cleaned)
            return params

    # ----------------------------------------
    # 3. City + State
    # ----------------------------------------
    city = req.city.strip() if req.city else None
    state = req.state.strip() if req.state else None

    if city and state:
        params["q"] = quote(f"{city}, {state}")
        return params

    # ----------------------------------------
    # 4. ZIP Code
    # ----------------------------------------
    if req.zip:
        zipcode = req.zip.strip()
        if zipcode:
            # OpenCage strongly recommends including a country context.
            params["q"] = quote(f"{zipcode}, USA")
            return params

    # ----------------------------------------
    # If nothing provided
    # ----------------------------------------
    params["q"] = ""  # or raise an exception depending on your design

    return params
