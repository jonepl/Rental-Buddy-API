from __future__ import annotations

from typing import Dict, List, Union

from fastapi import APIRouter

from app.domain.analytics import compute_metrics
from app.domain.dto.comps import (CompRow, CompsRequestByIds,
                                   CompsRequestInline, CompsResponse)
from app.services.result_cache import result_cache

router = APIRouter()


@router.post("/comps", response_model=CompsResponse)
async def comps_by_ids(
    req: Union[CompsRequestByIds, CompsRequestInline]
) -> CompsResponse:
    # Support inline and by-ids (from server cache)
    start = __import__("time").perf_counter()
    assumptions: Dict = (
        (req.assumptions or {}).__dict__ if hasattr(req, "assumptions") else {}
    )

    listings: List[Dict] = []
    source = "inline"
    if hasattr(req, "listings"):
        listings = [l.model_dump(by_alias=True) for l in req.listings]  # type: ignore
    elif hasattr(req, "ids"):
        source = "cache"
        for id_ in req.ids:  # type: ignore
            nl = result_cache.get_listing("last", id_)
            if nl is not None:
                listings.append(nl.model_dump(by_alias=True))

    rows: List[CompRow] = []
    for l in listings[: req.limit]:
        derived = compute_metrics(l, assumptions)
        rows.append(
            CompRow(
                id=l.get("id"),
                address=(l.get("address", {}) or {}).get("formatted"),
                facts={
                    "beds": (l.get("facts", {}) or {}).get("beds"),
                    "baths": (l.get("facts", {}) or {}).get("baths"),
                    "sqft": (l.get("facts", {}) or {}).get("sqft"),
                    "type": (l.get("facts", {}) or {}).get("property_type"),
                },
                base={
                    "category": l.get("category"),
                    "list_price": (l.get("pricing", {}) or {}).get("list_price"),
                },
                derived=derived,
            )
        )

    return CompsResponse(
        input={
            "count": len(listings),
            "metrics": list(rows[0].derived.keys()) if rows else [],
        },
        rows=rows,
        summary={"by_group": {}, "global": {"n": len(listings)}},
        meta={
            "duration_ms": int((__import__("time").perf_counter() - start) * 1000),
            "source": source,
        },
    )
