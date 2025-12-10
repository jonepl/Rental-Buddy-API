from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends

from app.api.deps import get_listings_service
from app.api.errors import handle_provider_error
from app.api.presenters.listings_presenter import create_response
from app.core.telemetry import request_id
from app.domain.dto.listings import (ListingsRequest, ListingsResponse,
                                     SalesListingsResponse)
from app.domain.dto.metrics import SalesMarketMetrics
from app.domain.enums.context_request import OperationType
from app.domain.sales_metrics import compute_sales_metrics
from app.services.listings_service import ListingsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sales", response_model=SalesListingsResponse)
async def sales(
    req: ListingsRequest,
    listings_service: ListingsService = Depends(get_listings_service),
) -> SalesListingsResponse:
    rid = request_id()
    start = time.perf_counter()

    try:
        listings = await listings_service.get_sale_data(req)

    except Exception as e:
        raise handle_provider_error(e, OperationType.SALES.value, rid)

    base_response = create_response(listings, req, OperationType.SALES, rid, start)
    metrics = compute_sales_metrics(base_response.listings)
    return SalesListingsResponse(
        **base_response.model_dump(),
        sales_metrics=metrics,
    )
