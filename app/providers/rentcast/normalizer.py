from __future__ import annotations

from typing import Any, Dict, List, Literal

from app.domain.dto import (
    Address,
    Dates,
    Facts,
    NormalizedListing,
    Pricing,
    ProviderInfo,
)


def normalize_rentcast_listing(
    raw: Dict[str, Any], category: Literal["rental", "sale"]
) -> NormalizedListing:
    address = Address(
        formatted=raw.get("formattedAddress") or raw.get("address"),
        line1=raw.get("line1") or None,
        line2=raw.get("line2") or None,
        city=raw.get("city") or None,
        state=raw.get("state") or None,
        zip=raw.get("zip") or None,
        county=raw.get("county") or None,
        county_fips=raw.get("county_fips") or None,
        lat=raw.get("latitude") or raw.get("lat"),
        lon=raw.get("longitude") or raw.get("lon"),
    )

    facts = Facts(
        beds=raw.get("bedrooms"),
        baths=raw.get("bathrooms"),
        sqft=raw.get("squareFootage") or raw.get("sqft"),
        year_built=raw.get("year_built"),
        property_type=raw.get("property_type"),
    )

    pricing = Pricing(
        list_price=raw.get("price"),
        currency="USD",
        period="monthly" if category == "rental" else "total",
    )

    dates = Dates(
        listed=raw.get("listed"),
        removed=raw.get("removed"),
        last_seen=raw.get("last_seen") or raw.get("updated_date"),
    )

    nid = raw.get("id") or raw.get("listing_id") or raw.get("mls_number") or "unknown"
    normalized_id = f"prov:rentcast:{nid}"

    nl = NormalizedListing(
        id=normalized_id,
        category=category,
        status=raw.get("status"),
        address=address,
        facts=facts,
        pricing=pricing,
        dates=dates,
        hoa={"monthly": raw.get("hoaFee") or 0},  # type: ignore
        distance_miles=None,
        provider=ProviderInfo(name="rentcast"),
    )
    return nl


def normalize_rentcast_response(
    rows: List[Dict[str, Any]], category: Literal["rental", "sale"]
) -> List[NormalizedListing]:
    return [normalize_rentcast_listing(r, category) for r in rows]
