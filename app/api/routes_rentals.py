from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.core.pagination import paginate, slice_page
from app.core.telemetry import duration_ms, request_id
from app.domain.dto import (
    ListingsEnvelope,
    NormalizedListing,
    SearchInputSummary,
    SearchRequest,
    EnvelopeSummary,
    EnvelopeMeta,
    PageSpec,
    Center,
    InputFilters,
)
from app.services.geocoding_service import GeocodingService
from app.services.property_service import PropertyService
from app.services.providers.rentcast import normalize_rentcast_response
from app.services.result_cache import result_cache
from app.utils.distance import haversine_distance

logger = logging.getLogger(__name__)

router = APIRouter()
geocoder = GeocodingService()


@router.post("/rentals", response_model=ListingsEnvelope)
async def rentals(req: SearchRequest) -> ListingsEnvelope:
    rid = request_id()
    start = __import__("time").perf_counter()

    # Resolve center (address XOR lat/lon; if both, address wins)
    lat: Optional[float] = None
    lon: Optional[float] = None
    resolved_addr: Optional[str] = None
    if req.address:
        g_lat, g_lon, g_formatted = await geocoder.geocode_address(req.address)
        if g_lat is None or g_lon is None:
            raise HTTPException(status_code=400, detail={"error": {"code": "400_INVALID_INPUT", "message": g_formatted or "Could not resolve address", "details": {}}})
        lat, lon, resolved_addr = g_lat, g_lon, g_formatted
    else:
        lat, lon, resolved_addr = req.latitude, req.longitude, f"Location at {req.latitude}, {req.longitude}"
        if lat is None or lon is None:
            raise HTTPException(status_code=400, detail={"error": {"code": "400_INVALID_INPUT", "message": "Invalid location", "details": {}}})

    service = PropertyService()
    raw_listings = await service.get_rental_data(
        latitude=lat,
        longitude=lon,
        bedrooms=req.beds,
        bathrooms=req.baths,
        radius_miles=req.radius_miles,
        days_old=req.days_old,
    )

    normalized: List[NormalizedListing] = normalize_rentcast_response(
        [l.model_dump() for l in raw_listings], "rental"
    )

    # compute distance
    for n in normalized:
        if n.address.lat is not None and n.address.lon is not None:
            n.distance_miles = haversine_distance(lat, lon, n.address.lat, n.address.lon)

    # filters
    def passes_filters(n: NormalizedListing) -> bool:
        price = n.pricing.list_price
        sqft = n.facts.sqft
        if req.min_price is not None and (price is None or price < req.min_price):
            return False
        if req.max_price is not None and (price is None or price > req.max_price):
            return False
        if req.min_sqft is not None and (sqft is None or sqft < req.min_sqft):
            return False
        if req.max_sqft is not None and (sqft is None or sqft > req.max_sqft):
            return False
        return True

    normalized = [n for n in normalized if passes_filters(n)]

    # dedupe by formatted address or lat/lon within ~25m
    seen_addr = set()
    deduped: List[NormalizedListing] = []
    for n in normalized:
        key = (n.address.formatted or "").strip().lower()
        if key:
            if key in seen_addr:
                continue
            seen_addr.add(key)
            deduped.append(n)
        else:
            # proximity dedupe
            duplicate = False
            for d in deduped:
                if n.address.lat is not None and n.address.lon is not None and d.address.lat is not None and d.address.lon is not None:
                    if haversine_distance(n.address.lat, n.address.lon, d.address.lat, d.address.lon) <= 0.016:
                        duplicate = True
                        break
            if not duplicate:
                deduped.append(n)

    # sort
    reverse = (req.sort.dir == "desc")
    if req.sort.by == "distance":
        deduped.sort(key=lambda x: (x.distance_miles is None, x.distance_miles or 0), reverse=reverse)
    elif req.sort.by == "price":
        deduped.sort(key=lambda x: (x.pricing.list_price is None, x.pricing.list_price or 0), reverse=reverse)
    elif req.sort.by == "beds":
        deduped.sort(key=lambda x: (x.facts.beds is None, x.facts.beds or 0), reverse=reverse)
    elif req.sort.by == "baths":
        deduped.sort(key=lambda x: (x.facts.baths is None, x.facts.baths or 0), reverse=reverse)
    elif req.sort.by == "sqft":
        deduped.sort(key=lambda x: (x.facts.sqft is None, x.facts.sqft or 0), reverse=reverse)

    # cache full normalized array; paginate from cache
    result_cache.put("last", center_lat=lat, center_lon=lon, category="rental", listings=deduped)

    total = len(deduped)
    page_items = slice_page(deduped, req.limit, req.offset)
    returned, limit, next_offset = paginate(total, req.limit, req.offset)

    total = len(normalized)

    env = ListingsEnvelope(
        input=SearchInputSummary(
            center=Center(lat=lat, lon=lon),
            radius_miles=req.radius_miles,
            filters=InputFilters(beds=req.beds, baths=req.baths, days_old=req.days_old),
        ),
        summary=EnvelopeSummary(
            returned=returned, count=None, page=PageSpec(limit=limit, offset=req.offset, next_offset=next_offset)
        ),
        listings=page_items,
        meta=EnvelopeMeta(
            category="rental",
            request_id=rid,
            duration_ms=duration_ms(start),
            cache="miss",
            provider_calls=1,
        ),
    )
    return env
