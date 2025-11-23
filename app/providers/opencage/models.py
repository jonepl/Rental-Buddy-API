from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class License(BaseModel):
    name: str
    url: str


class Rate(BaseModel):
    limit: int
    remaining: int
    reset: int


class LatLng(BaseModel):
    lat: float
    lng: float


class Bounds(BaseModel):
    northeast: LatLng
    southwest: LatLng


class Components(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    iso_3166_1_alpha_2: Optional[str] = Field(alias="ISO_3166-1_alpha-2", default=None)
    iso_3166_1_alpha_3: Optional[str] = Field(alias="ISO_3166-1_alpha-3", default=None)
    iso_3166_2: Optional[List[str]] = Field(alias="ISO_3166-2", default=None)

    # Special underscored keys
    category: Optional[str] = Field(alias="_category", default=None)
    normalized_city: Optional[str] = Field(alias="_normalized_city", default=None)
    place_type: Optional[str] = Field(alias="_type", default=None)

    # Common address fields
    city: Optional[str] = None
    continent: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    postcode: Optional[str] = None
    road: Optional[str] = None
    road_type: Optional[str] = None
    state: Optional[str] = None
    suburb: Optional[str] = None


class DistanceFromQ(BaseModel):
    meters: float


class Geometry(BaseModel):
    lat: float
    lng: float


class Result(BaseModel):
    # Rich structured data, but you can keep it as a dict for now
    annotations: Optional[dict[str, Any]] = None

    bounds: Optional[Bounds] = None
    components: Components
    confidence: Optional[int] = None
    distance_from_q: Optional[DistanceFromQ] = None
    formatted: str
    geometry: Geometry


class Status(BaseModel):
    code: int
    message: str


class StayInformed(BaseModel):
    blog: Optional[str] = None
    mastodon: Optional[str] = None


class Timestamp(BaseModel):
    created_http: str
    created_unix: int


class GeocodeResponse(BaseModel):
    documentation: str
    licenses: List[License]
    rate: Rate
    results: List[Result]
    status: Status
    stay_informed: Optional[StayInformed] = None
    thanks: Optional[str] = None
    timestamp: Timestamp
    total_results: int
