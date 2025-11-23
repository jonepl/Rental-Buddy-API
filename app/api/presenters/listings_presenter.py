from __future__ import annotations

from typing import List

from app.core.pagination import paginate, slice_page
from app.core.telemetry import duration_ms
from app.domain.dto import (Center, EnvelopeMeta, EnvelopeSummary,
                            InputFilters, ListingsRequest, ListingsResponse,
                            NormalizedListing, PageSpec, SearchInputSummary)
from app.domain.enums.context_request import OperationType


def create_response(
    listings: List[NormalizedListing],
    req: ListingsRequest,
    context: OperationType,
    rid: str,
    start: float,
) -> ListingsResponse:
    total = len(listings)
    page_items = slice_page(listings, req.limit, req.offset)
    returned, limit, next_offset = paginate(total, req.limit, req.offset)

    env = ListingsResponse(
        input=SearchInputSummary.generate_input_summary(req),
        summary=EnvelopeSummary(
            returned=returned,
            count=None,
            page=PageSpec(limit=limit, offset=req.offset, next_offset=next_offset),
        ),
        listings=page_items,
        meta=EnvelopeMeta(
            category=context.value,
            request_id=rid,
            duration_ms=duration_ms(start),
            cache="miss",
            provider_calls=1,
        ),
    )

    return env
