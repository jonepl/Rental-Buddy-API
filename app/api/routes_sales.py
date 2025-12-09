from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends

from app.api.deps import get_listings_service
from app.api.errors import handle_provider_error
from app.api.presenters.listings_presenter import create_response
from app.core.telemetry import request_id
from app.domain.dto.listings import ListingsRequest, ListingsResponse
from app.domain.enums.context_request import OperationType
from app.services.listings_service import ListingsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sales", response_model=ListingsResponse)
async def sales(
    req: ListingsRequest,
    listings_service: ListingsService = Depends(get_listings_service),
) -> ListingsResponse:
    rid = request_id()
    start = time.perf_counter()

    try:
        listings = await listings_service.get_sale_data(req)

    except Exception as e:
        raise handle_provider_error(e, OperationType.SALES.value, rid)

    return create_response(listings, req, OperationType.SALES, rid, start)
