from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.range_types import Range
from app.domain.dto.metrics import RentalMarketMetrics, SalesMarketMetrics


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
    beds: Optional[Range[int]] = None
    baths: Optional[Range[float]] = None
    price: Optional[Range[float]] = None
    sqft: Optional[Range[int]] = None
    year_built: Optional[Range[int]] = None
    days_old: Optional[Range[int]] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: SortSpec = Field(default_factory=SortSpec)

    @model_validator(mode="after")
    def validate_location_input(self) -> "ListingsRequest":
        if (
            not self.address
            and (self.latitude is None or self.longitude is None)
            and (self.city is None or self.state is None)
            and self.zip is None
        ):
            raise ValueError(
                "Must provide either address, latitude & longitude, or city + state"
            )

        br = self.baths
        if br is not None:
            for val in (br.min, br.max):
                if val is not None and (val * 2) % 1 != 0:
                    raise ValueError("baths values must be in 0.5 increments")

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
    def generate_input_summary(cls, request: ListingsRequest) -> "SearchInputSummary":
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


class RentalListingsResponse(ListingsResponse):
    rental_metrics: Optional[RentalMarketMetrics] = None


class SalesListingsResponse(ListingsResponse):
    sales_metrics: Optional[SalesMarketMetrics] = None


class CachedListings(BaseModel):
    items: List[NormalizedListing]
