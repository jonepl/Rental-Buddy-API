from app.api.routes_sales import ListingsRequest

FULL_REQUEST: ListingsRequest = {
    "address": "string",
    "latitude": 0,
    "longitude": 0,
    "radius_miles": 5,
    "beds": {"min": 0, "max": 3},
    "baths": {"min": 0.5, "max": 2},
    "price": {"min": 0, "max": 500000},
    "sqft": {"min": 0, "max": 4000},
    "year_built": {"min": 1950, "max": 2025},
    "days_old": {"min": 0, "max": 30},
    "limit": 50,
    "offset": 0,
    "sort": {"by": "distance", "dir": "asc"},
}
