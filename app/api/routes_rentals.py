from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends

from app.api.deps import get_listings_service
from app.api.errors import handle_provider_error
from app.api.presenters.listings_presenter import create_response
from app.core.telemetry import request_id
from app.domain.dto.listings import (ListingsRequest, ListingsResponse,
                                     RentalListingsResponse)
from app.domain.dto.metrics import RentalMarketMetrics
from app.domain.enums.context_request import OperationType
from app.domain.regional_metrics import compute_regional_metrics
from app.services.listings_service import ListingsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rentals", response_model=RentalListingsResponse)
async def rentals(
    req: ListingsRequest,
    listings_service: ListingsService = Depends(get_listings_service),
) -> RentalListingsResponse:
    rid = request_id()
    start = time.perf_counter()

    try:
        listings = await listings_service.get_rental_data(req)

    except Exception as e:
        raise handle_provider_error(e, OperationType.RENTALS.value, rid)

    base_response = create_response(listings, req, OperationType.RENTALS, rid, start)
    metrics = compute_regional_metrics(
        base_response.listings, req.latitude, req.longitude
    )
    return RentalListingsResponse(
        **base_response.model_dump(),
        rental_metrics=metrics,
    )

# TODO: This logic may be merged with rentals.
@router.post("/rentals/regional-metrics", response_model=RentalMarketMetrics)
async def rentals_regional_metrics(
    req: ListingsRequest,
    listings_service: ListingsService = Depends(get_listings_service),
) -> RentalMarketMetrics:
    rid = request_id()
    start = time.perf_counter()

    try:
        metrics = await listings_service.get_regional_metrics(req)
    except Exception as e:
        raise handle_provider_error(e, OperationType.RENTALS.value, rid)

    logger.info(
        "computed regional metrics",
        extra={"request_id": rid, "duration_ms": (time.perf_counter() - start) * 1000},
    )
    return metrics
