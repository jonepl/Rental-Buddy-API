from __future__ import annotations

from typing import List, Literal, Optional

from app.domain.dto import (HOA, Address, Dates, Facts, ListingsRequest,
                            NormalizedListing, Pricing, ProviderInfo)


def make_listing(
    listing_id: str,
    price: float,
    beds: int,
    baths: float,
    sqft: int,
    lat: float,
    lon: float,
    formatted: Optional[str] = None,
    category: Literal["rental", "sale"] = "rental",
) -> NormalizedListing:
    return NormalizedListing(
        id=listing_id,
        category=category,
        status="Active",
        address=Address(formatted=formatted, lat=lat, lon=lon),
        facts=Facts(beds=beds, baths=baths, sqft=sqft),
        pricing=Pricing(list_price=price),
        dates=Dates(),
        hoa=HOA(),
        provider=ProviderInfo(name="RentCast"),
    )


class StubListingsService:
    def __init__(
        self,
        listings: Optional[List[NormalizedListing]] = None,
        error: Exception | None = None,
    ):
        self.listings = listings or []
        self.error = error
        self.requests: List[ListingsRequest] = []

    async def get_sale_data(self, request: ListingsRequest) -> List[NormalizedListing]:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.listings

    async def get_rental_data(
        self, request: ListingsRequest
    ) -> List[NormalizedListing]:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.listings
