from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.domain.dto.listings import NormalizedListing


class CompsAssumptions(BaseModel):
    vacancy_pct: Optional[float] = 5
    maintenance_pct_of_rent: Optional[float] = 8
    mgmt_pct_of_rent: Optional[float] = 8
    taxes_annual: Optional[float] = None
    insurance_annual: Optional[float] = None
    hoa_monthly: Optional[float] = None
    purchase_price: Optional[float] = None
    market_rent: Optional[float] = None


class CompsRequestByIds(BaseModel):
    ids: List[str]
    assumptions: Optional[CompsAssumptions] = None
    metrics: List[str]
    group_by: Optional[List[str]] = None
    limit: int = 100


class CompsRequestInline(BaseModel):
    listings: List[NormalizedListing]
    assumptions: Optional[CompsAssumptions] = None
    metrics: List[str]
    group_by: Optional[List[str]] = None
    limit: int = 100


class CompRow(BaseModel):
    id: str
    address: Optional[str] = None
    facts: Dict[str, Any]
    base: Dict[str, Any]
    derived: Dict[str, Optional[float]]
    ranks: Dict[str, Optional[float]] = Field(default_factory=dict)


class CompsSummary(BaseModel):
    by_group: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    global_: Dict[str, Any] = Field(default_factory=dict, alias="global")


class CompsResponse(BaseModel):
    input: Dict[str, Any]
    rows: List[CompRow]
    summary: CompsSummary
    meta: Dict[str, Any]
