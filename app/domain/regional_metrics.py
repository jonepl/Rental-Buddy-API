from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from statistics import mean, median
from typing import Dict, List, Optional, Sequence, Tuple

from app.domain.dto.listings import NormalizedListing
from app.domain.dto.metrics import (ClusterRentStats, DistanceMetrics,
                                    OverallRentMetrics, PropertyTypeStats,
                                    RentalMarketMetrics)
from app.utils.distance import haversine_distance


def compute_regional_metrics(
    rentals: List[NormalizedListing],
    center_lat: Optional[float],
    center_lon: Optional[float],
) -> RentalMarketMetrics:
    rents: List[float] = []
    rent_per_sqft_values: List[float] = []
    days_on_market_values: List[int] = []
    distance_values: List[float] = []
    rent_distance_pairs: List[Tuple[float, float]] = []

    property_groups: Dict[str, List[Dict[str, Optional[float]]]] = defaultdict(list)
    zip_groups: Dict[str, List[Dict[str, Optional[float]]]] = defaultdict(list)

    for listing in rentals:
        rent = listing.pricing.list_price
        sqft = _positive_number(listing.facts.sqft)
        rent_per_sqft = _safe_div(rent, sqft)
        dom = _compute_days_on_market(listing)
        distance = _listing_distance(listing, center_lat, center_lon)

        if rent is not None:
            rents.append(rent)
        if rent_per_sqft is not None:
            rent_per_sqft_values.append(rent_per_sqft)
        if dom is not None:
            days_on_market_values.append(dom)
        if distance is not None:
            distance_values.append(distance)
            if rent is not None:
                rent_distance_pairs.append((rent, distance))

        property_key = listing.facts.property_type or "unknown"
        property_groups[property_key].append(
            {
                "rent": rent,
                "rent_per_sqft": rent_per_sqft,
                "sqft": sqft,
                "dom": None if dom is None else float(dom),
            }
        )

        zip_key = listing.address.zip or "unknown"
        zip_groups[zip_key].append(
            {
                "rent": rent,
                "rent_per_sqft": rent_per_sqft,
            }
        )

    overall_metrics = OverallRentMetrics(
        count=len(rentals),
        min_rent=_min_value(rents),
        max_rent=_max_value(rents),
        mean_rent=_mean_value(rents),
        median_rent=_median_value(rents),
        p25_rent=_percentile_value(rents, 0.25),
        p75_rent=_percentile_value(rents, 0.75),
        min_rent_per_sqft=_min_value(rent_per_sqft_values),
        max_rent_per_sqft=_max_value(rent_per_sqft_values),
        mean_rent_per_sqft=_mean_value(rent_per_sqft_values),
        median_rent_per_sqft=_median_value(rent_per_sqft_values),
        p25_rent_per_sqft=_percentile_value(rent_per_sqft_values, 0.25),
        p75_rent_per_sqft=_percentile_value(rent_per_sqft_values, 0.75),
        mean_days_on_market=_mean_value(days_on_market_values),
        median_days_on_market=_median_value(days_on_market_values),
        fastest_days_on_market=_min_int(days_on_market_values),
        slowest_days_on_market=_max_int(days_on_market_values),
    )

    distance_metrics = DistanceMetrics(
        median_distance_miles=_median_value(distance_values),
        rent_distance_correlation=_pearson_correlation(rent_distance_pairs),
        distance_weighted_median_rent=_distance_weighted_median(rent_distance_pairs),
    )

    property_type_metrics = [
        _build_property_stats(property_type, entries)
        for property_type, entries in sorted(property_groups.items())
    ]

    clusters_by_zip = [
        _build_cluster_stats(cluster_key, entries)
        for cluster_key, entries in sorted(zip_groups.items())
    ]

    return RentalMarketMetrics(
        overall=overall_metrics,
        distance=distance_metrics,
        property_type_metrics=property_type_metrics,
        clusters_by_zip=clusters_by_zip,
    )


def _positive_number(value: Optional[int]) -> Optional[float]:
    if value is None:
        return None
    if value <= 0:
        return None
    return float(value)


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    try:
        return a / b
    except ZeroDivisionError:
        return None


def _listing_distance(
    listing: NormalizedListing,
    center_lat: Optional[float],
    center_lon: Optional[float],
) -> Optional[float]:
    if listing.distance_miles is not None:
        return listing.distance_miles
    if center_lat is None or center_lon is None:
        return None
    lat = listing.address.lat
    lon = listing.address.lon
    if lat is None or lon is None:
        return None
    try:
        return haversine_distance(center_lat, center_lon, lat, lon)
    except ValueError:
        return None


def _compute_days_on_market(listing: NormalizedListing) -> Optional[int]:
    listed = _parse_date(listing.dates.listed)
    end = _parse_date(listing.dates.removed) or _parse_date(listing.dates.last_seen)
    if listed is None or end is None:
        return None
    delta = (end - listed).days
    if delta < 0:
        return None
    return delta


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    iso_candidate = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate)
    except ValueError:
        pass

    patterns = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def _min_value(values: Sequence[float]) -> Optional[float]:
    return min(values) if values else None


def _max_value(values: Sequence[float]) -> Optional[float]:
    return max(values) if values else None


def _mean_value(values: Sequence[float]) -> Optional[float]:
    return mean(values) if values else None


def _median_value(values: Sequence[float]) -> Optional[float]:
    return median(values) if values else None


def _percentile_value(values: Sequence[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return sorted_values[int(rank)]
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    return lower_value * (upper - rank) + upper_value * (rank - lower)


def _min_int(values: Sequence[int]) -> Optional[int]:
    return int(min(values)) if values else None


def _max_int(values: Sequence[int]) -> Optional[int]:
    return int(max(values)) if values else None


def _pearson_correlation(pairs: Sequence[Tuple[float, float]]) -> Optional[float]:
    if len(pairs) < 2:
        return None
    rents = [p[0] for p in pairs]
    distances = [p[1] for p in pairs]
    mean_rent = mean(rents)
    mean_distance = mean(distances)

    numerator = sum((r - mean_rent) * (d - mean_distance) for r, d in pairs)
    rent_variance = sum((r - mean_rent) ** 2 for r in rents)
    distance_variance = sum((d - mean_distance) ** 2 for d in distances)
    denominator = math.sqrt(rent_variance * distance_variance)
    if denominator == 0:
        return None
    return numerator / denominator


def _distance_weighted_median(pairs: Sequence[Tuple[float, float]]) -> Optional[float]:
    if not pairs:
        return None
    weights_pairs = []
    total_weight = 0.0
    for rent, distance in pairs:
        adj_distance = distance if distance is not None else 0.0
        weight = 1.0 / (abs(adj_distance) + 0.1)
        weights_pairs.append((rent, weight))
        total_weight += weight
    if total_weight == 0:
        return None

    threshold = total_weight / 2.0
    running = 0.0
    for rent, weight in sorted(weights_pairs, key=lambda x: x[0]):
        running += weight
        if running >= threshold:
            return rent
    return weights_pairs[-1][0]


def _build_property_stats(
    property_type: str, entries: Sequence[Dict[str, Optional[float]]]
) -> PropertyTypeStats:
    rent_values = [entry["rent"] for entry in entries if entry["rent"] is not None]
    rent_per_sqft_values = [
        entry["rent_per_sqft"]
        for entry in entries
        if entry["rent_per_sqft"] is not None
    ]
    sqft_values = [entry["sqft"] for entry in entries if entry["sqft"] is not None]
    dom_values = [entry["dom"] for entry in entries if entry["dom"] is not None]

    return PropertyTypeStats(
        property_type=property_type,
        count=len(entries),
        median_rent=_median_value(rent_values),
        median_rent_per_sqft=_median_value(rent_per_sqft_values),
        median_sqft=_median_value(sqft_values),
        mean_days_on_market=_mean_value(dom_values),
    )


def _build_cluster_stats(
    cluster_key: str, entries: Sequence[Dict[str, Optional[float]]]
) -> ClusterRentStats:
    rent_values = [entry["rent"] for entry in entries if entry["rent"] is not None]
    rent_per_sqft_values = [
        entry["rent_per_sqft"]
        for entry in entries
        if entry["rent_per_sqft"] is not None
    ]
    return ClusterRentStats(
        cluster_key=cluster_key,
        count=len(entries),
        median_rent=_median_value(rent_values),
        median_rent_per_sqft=_median_value(rent_per_sqft_values),
    )
