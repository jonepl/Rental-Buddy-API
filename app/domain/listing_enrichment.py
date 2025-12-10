from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.domain.dto.listings import NormalizedListing
from app.utils.distance import haversine_distance

FRESH_THRESHOLD_DAYS = 14
STALE_THRESHOLD_DAYS = 60


def enrich_listings(
    listings: List[NormalizedListing],
    center_lat: Optional[float],
    center_lon: Optional[float],
) -> None:
    for listing in listings:
        _annotate_price_per_sqft(listing)
        _annotate_dom_flags(listing)
        _annotate_hoa(listing)
        _annotate_distance(listing, center_lat, center_lon)


def _annotate_price_per_sqft(listing: NormalizedListing) -> None:
    price = listing.pricing.list_price
    sqft = listing.facts.sqft
    listing.pricing.price_per_sqft = _safe_div(price, sqft)


def _annotate_dom_flags(listing: NormalizedListing) -> None:
    dom = listing.dates.days_on_market
    if dom is None:
        dom = _compute_days_on_market(
            listing.dates.listed, listing.dates.removed, listing.dates.last_seen
        )
        listing.dates.days_on_market = dom
    listing.dates.is_fresh = _flag_dom(dom, FRESH_THRESHOLD_DAYS, "le")
    listing.dates.is_stale = _flag_dom(dom, STALE_THRESHOLD_DAYS, "ge")


def _annotate_hoa(listing: NormalizedListing) -> None:
    monthly = listing.hoa.monthly
    if monthly is None:
        listing.hoa.has_hoa = None
    else:
        listing.hoa.has_hoa = monthly != 0


def _annotate_distance(
    listing: NormalizedListing,
    center_lat: Optional[float],
    center_lon: Optional[float],
) -> None:
    if center_lat is None or center_lon is None:
        return
    lat = listing.address.lat
    lon = listing.address.lon
    if lat is None or lon is None:
        return
    try:
        listing.distance_miles = haversine_distance(center_lat, center_lon, lat, lon)
    except ValueError:
        listing.distance_miles = None


def _compute_days_on_market(
    listed: Optional[str], removed: Optional[str], last_seen: Optional[str]
) -> Optional[int]:
    start = _parse_date(listed)
    end = _parse_date(removed) or _parse_date(last_seen)
    if start is None or end is None:
        return None
    delta = (end - start).days
    if delta < 0:
        return None
    return delta


def _flag_dom(dom: Optional[int], threshold: int, mode: str) -> Optional[bool]:
    if dom is None:
        return None
    if mode == "le":
        return dom <= threshold
    return dom >= threshold


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return None


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    for pattern in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
