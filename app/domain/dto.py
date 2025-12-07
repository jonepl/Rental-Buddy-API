from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)

from app.domain.range_types import Range


class SortBy(str, Enum):
    distance = "distance"
    price = "price"
    beds = "beds"
    baths = "baths"
    sqft = "sqft"


class SortSpec(BaseModel):
    by: SortBy = SortBy.distance
    dir: Literal["asc", "desc"] = "asc"


class ListingsRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_miles: float = Field(default=5.0, gt=0)
    # range-only fields (object form)
    beds: Optional[Range[int]] = None
    baths: Optional[Range[float]] = None
    price: Optional[Range[float]] = None
    sqft: Optional[Range[int]] = None
    year_built: Optional[Range[int]] = None
    days_old: Optional[Range[int]] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: SortSpec = Field(default_factory=SortSpec)

    # no scalar baths validation now; enforce step on baths range in model_validator

    @model_validator(mode="after")
    def validate_location_input(self) -> "ListingsRequest":
        # address XOR (lat & lon). If both, address wins but it's still valid
        if (
            not self.address
            and (self.latitude is None or self.longitude is None)
            and (self.city is None or self.state is None)
            and self.zip is None
        ):
            raise ValueError(
                "Must provide either address, latitude & longitude, or city + state"
            )
        # baths must adhere to 0.5 increments if provided
        br = self.baths
        if br is not None:
            for val in (br.min, br.max):
                if val is not None and (val * 2) % 1 != 0:
                    raise ValueError("baths values must be in 0.5 increments")
        # generic min <= max checks
        for r in (
            self.beds,
            self.baths,
            self.price,
            self.sqft,
            self.year_built,
            self.days_old,
        ):
            if (
                r is not None
                and r.min is not None
                and r.max is not None
                and r.min > r.max
            ):
                raise ValueError("range min cannot be greater than max")
        return self


class Center(BaseModel):
    lat: float
    lon: float


class InputFilters(BaseModel):
    beds: Optional[int] = None
    baths: Optional[float] = None
    days_old: Optional[str] = None


class PageSpec(BaseModel):
    limit: int
    offset: int
    next_offset: Optional[int] = None


class SearchInputSummary(BaseModel):
    center: Optional[Center] = None
    radius_miles: Optional[float] = None
    filters: InputFilters
    location: Optional[str] = None

    @classmethod
    def generate_input_summary(cls, request: ListingsRequest) -> SearchInputSummary:
        # prefer the most specific location the user supplied
        location = request.address or None
        if location is None and request.city and request.state:
            location = f"{request.city}, {request.state}"
        if location is None and request.zip:
            location = request.zip

        filters = InputFilters(
            beds=request.beds.min if request.beds else None,
            baths=request.baths.min if request.baths else None,
            days_old=str(request.days_old.min)
            if request.days_old and request.days_old.min is not None
            else None,
        )

        center = (
            Center(lat=request.latitude, lon=request.longitude)
            if request.latitude and request.longitude
            else None
        )

        return cls(
            center=center,
            radius_miles=request.radius_miles,
            location=location,
            filters=filters,
        )


class ProviderInfo(BaseModel):
    name: Literal["RentCast", "OpenCage"]


class Address(BaseModel):
    formatted: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    county: Optional[str] = None
    county_fips: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class Facts(BaseModel):
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None


class Pricing(BaseModel):
    list_price: Optional[float] = None
    currency: str = "USD"
    period: Optional[Literal["monthly", "total"]] = None


class Dates(BaseModel):
    listed: Optional[str] = None
    removed: Optional[str] = None
    last_seen: Optional[str] = None


class HOA(BaseModel):
    monthly: Optional[float] = None


class NormalizedListing(BaseModel):
    id: str
    category: Literal["rental", "sale"]
    status: Optional[str] = None
    address: Address
    facts: Facts
    pricing: Pricing
    dates: Dates = Field(default_factory=Dates)
    hoa: HOA = Field(default_factory=HOA)
    distance_miles: Optional[float] = None
    provider: ProviderInfo = Field(
        default_factory=lambda: ProviderInfo(name="RentCast")
    )


class EnvelopeSummary(BaseModel):
    returned: int
    count: Optional[int] = None
    page: PageSpec


class OverallRentMetrics(BaseModel):
    count: int
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    mean_rent: Optional[float] = None
    median_rent: Optional[float] = None
    p25_rent: Optional[float] = None
    p75_rent: Optional[float] = None

    min_rent_per_sqft: Optional[float] = None
    max_rent_per_sqft: Optional[float] = None
    mean_rent_per_sqft: Optional[float] = None
    median_rent_per_sqft: Optional[float] = None
    p25_rent_per_sqft: Optional[float] = None
    p75_rent_per_sqft: Optional[float] = None

    mean_days_on_market: Optional[float] = None
    median_days_on_market: Optional[float] = None
    fastest_days_on_market: Optional[int] = None
    slowest_days_on_market: Optional[int] = None


class DistanceMetrics(BaseModel):
    median_distance_miles: Optional[float] = None
    rent_distance_correlation: Optional[float] = None
    distance_weighted_median_rent: Optional[float] = None


class PropertyTypeStats(BaseModel):
    property_type: str
    count: int
    median_rent: Optional[float] = None
    median_rent_per_sqft: Optional[float] = None
    median_sqft: Optional[float] = None
    mean_days_on_market: Optional[float] = None


class ClusterRentStats(BaseModel):
    cluster_key: str
    count: int
    median_rent: Optional[float] = None
    median_rent_per_sqft: Optional[float] = None


class RegionalMetrics(BaseModel):
    overall: OverallRentMetrics
    distance: DistanceMetrics
    property_type_metrics: List[PropertyTypeStats]
    clusters_by_zip: List[ClusterRentStats]


class EnvelopeMeta(BaseModel):
    category: Literal["rental", "sale"]
    request_id: str
    duration_ms: int
    cache: Literal["hit", "miss", "partial"]
    provider_calls: int


class ListingsResponse(BaseModel):
    input: SearchInputSummary
    summary: EnvelopeSummary
    listings: List[NormalizedListing]
    meta: EnvelopeMeta


class CachedListings(BaseModel):
    items: List[NormalizedListing]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class PropertyInvestmentMetrics(BaseModel):
    # Income
    market_rent_monthly: Optional[float] = None
    rent_low: Optional[float] = None
    rent_high: Optional[float] = None
    rent_per_sqft: Optional[float] = None
    rent_per_bedroom: Optional[float] = None
    rent_range_spread_pct: Optional[float] = None

    # Price/value
    purchase_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    rv_ratio_monthly: Optional[float] = None
    gross_yield: Optional[float] = None
    grm: Optional[float] = None
    delta_vs_area_median_price_pct: Optional[float] = None

    # Operations
    noi_annual: Optional[float] = None
    cap_rate: Optional[float] = None
    expense_ratio: Optional[float] = None  # operating_expenses / EGI

    # Standard financing scenario
    loan_amount_std: Optional[float] = None
    monthly_pi_std: Optional[float] = None
    dscr_std: Optional[float] = None
    monthly_cashflow_std: Optional[float] = None
    cash_on_cash_std: Optional[float] = None

    # Risk / quality indicators
    rent_uncertainty_score: Optional[float] = None
    comp_density_score: Optional[float] = None
    price_dispersion_score: Optional[float] = None


class PropertyInvestmentScore(BaseModel):
    overall_score: float  # 0–100
    cashflow_score: float
    value_score: float
    risk_score: float
    metrics: PropertyInvestmentMetrics


# COMPS
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
