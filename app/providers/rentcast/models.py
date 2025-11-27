# app/providers/rentcast/models.py
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class Builder(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    development: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None


class HOA(BaseModel):
    model_config = ConfigDict(extra="allow")
    fee: Optional[float] = None


class Contact(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class HistoryEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    event: Optional[str] = None
    price: Optional[float] = None
    listing_type: Optional[str] = Field(default=None, alias="listingType")
    listed_date: Optional[str] = Field(default=None, alias="listedDate")
    removed_date: Optional[str] = Field(default=None, alias="removedDate")
    days_on_market: Optional[int] = Field(default=None, alias="daysOnMarket")


class RentCastPropertyListing(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    formatted_address: Optional[str] = Field(alias="formattedAddress", default=None)
    address_line1: Optional[str] = Field(alias="addressLine1", default=None)
    address_line2: Optional[str] = Field(alias="addressLine2", default=None)
    city: Optional[str] = None
    state: Optional[str] = None
    state_fips: Optional[str] = Field(alias="stateFips", default=None)
    zip_code: Optional[str] = Field(alias="zipCode", default=None)
    county: Optional[str] = None
    county_fips: Optional[str] = Field(alias="countyFips", default=None)

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    property_type: Optional[str] = Field(alias="propertyType", default=None)
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = Field(alias="squareFootage", default=None)
    lot_size: Optional[int] = Field(alias="lotSize", default=None)
    year_built: Optional[int] = Field(alias="yearBuilt", default=None)
    hoa: Optional[HOA] = Field(alias="hoa", default=None)

    status: Optional[str] = None
    price: Optional[float] = None
    listing_type: Optional[str] = Field(alias="listingType", default=None)
    listed_date: Optional[str] = Field(alias="listedDate", default=None)
    removed_date: Optional[str] = Field(alias="removedDate", default=None)
    created_date: Optional[str] = Field(alias="createdDate", default=None)
    last_seen_date: Optional[str] = Field(alias="lastSeenDate", default=None)
    days_on_market: Optional[int] = Field(alias="daysOnMarket", default=None)

    mls_name: Optional[str] = Field(alias="mlsName", default=None)
    mls_number: Optional[str] = Field(alias="mlsNumber", default=None)

    listing_agent: Optional[Contact] = Field(alias="listingAgent", default=None)
    listing_office: Optional[Contact] = Field(alias="listingOffice", default=None)

    builder: Optional[Builder] = Field(alias="builder", default=None)

    # History is a dict keyed by date strings -> objects
    history: Optional[Dict[str, HistoryEntry]] = None
