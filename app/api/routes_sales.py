from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.core.pagination import paginate, slice_page
from app.core.telemetry import duration_ms, request_id
from app.domain.dto import (
    Center,
    EnvelopeMeta,
    EnvelopeSummary,
    InputFilters,
    ListingsEnvelope,
    NormalizedListing,
    PageSpec,
    SearchInputSummary,
    SearchRequest,
)
from app.domain.range_types import Range
from app.providers.rentcast.normalizer import normalize_rentcast_response
from app.services.geocoding_service import GeocodingService
from app.services.property_service import PropertyService
from app.services.result_cache import result_cache
from app.utils.distance import haversine_distance

logger = logging.getLogger(__name__)

router = APIRouter()
geocoder = GeocodingService()
property_service = PropertyService(geocoder)


@router.post("/sales", response_model=ListingsEnvelope)
async def sales(req: SearchRequest) -> ListingsEnvelope:
    rid = request_id()
    start = __import__("time").perf_counter()

    raw_listings, req_lat, req_lon = await property_service.get_sale_data(req)

    normalized: List[NormalizedListing] = normalize_rentcast_response(
        [l.model_dump() for l in raw_listings], "sale"
    )

    # calculate distance for each listing
    for norm in normalized:
        if norm.address.lat is not None and norm.address.lon is not None:
            norm.distance_miles = haversine_distance(
                req_lat, req_lon, norm.address.lat, norm.address.lon
            )

    deduped: List[NormalizedListing] = normalized

    # sort
    reverse = req.sort.dir == "desc"
    if req.sort.by == "distance":
        deduped.sort(
            key=lambda x: (x.distance_miles is None, x.distance_miles or 0),
            reverse=reverse,
        )
    elif req.sort.by == "price":
        deduped.sort(
            key=lambda x: (x.pricing.list_price is None, x.pricing.list_price or 0),
            reverse=reverse,
        )
    elif req.sort.by == "beds":
        deduped.sort(
            key=lambda x: (x.facts.beds is None, x.facts.beds or 0), reverse=reverse
        )
    elif req.sort.by == "baths":
        deduped.sort(
            key=lambda x: (x.facts.baths is None, x.facts.baths or 0), reverse=reverse
        )
    elif req.sort.by == "sqft":
        deduped.sort(
            key=lambda x: (x.facts.sqft is None, x.facts.sqft or 0), reverse=reverse
        )

    # cache full normalized array; paginate from cache
    result_cache.put(
        "last", center_lat=lat, center_lon=lon, category="sale", listings=deduped
    )

    total = len(deduped)
    page_items = slice_page(deduped, req.limit, req.offset)
    returned, limit, next_offset = paginate(total, req.limit, req.offset)

    env = ListingsEnvelope(
        input=SearchInputSummary(
            center=Center(lat=lat, lon=lon),
            radius_miles=req.radius_miles,
            filters=InputFilters(
                beds=(req.beds.min if req.beds is not None else None),
                baths=(req.baths.min if req.baths is not None else None),
                days_old=(
                    str(req.days_old.min)
                    if (req.days_old is not None and req.days_old.min is not None)
                    else None
                ),
            ),
        ),
        summary=EnvelopeSummary(
            returned=returned,
            count=None,
            page=PageSpec(limit=limit, offset=req.offset, next_offset=next_offset),
        ),
        listings=page_items,
        meta=EnvelopeMeta(
            category="sale",
            request_id=rid,
            duration_ms=duration_ms(start),
            cache="miss",
            provider_calls=1,
        ),
    )
    return env
