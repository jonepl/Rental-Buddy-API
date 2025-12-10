from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from statistics import mean, median, pstdev
from typing import Dict, List, Optional, Sequence

from app.domain.dto.listings import NormalizedListing
from app.domain.dto.metrics import (HoaFeeMetrics, OverallSalesMetrics,
                                    PriceDistributionMetrics,
                                    PricePerSqftDistributionMetrics,
                                    PriceBucket, SalesMarketMetrics,
                                    SalesOutlierMetrics,
                                    SalesPropertyTypeStats,
                                    SalesZipClusterStats,
                                    SizeAndAgeMetrics)


def compute_sales_metrics(listings: List[NormalizedListing]) -> SalesMarketMetrics:
    prices = _collect_prices(listings)
    price_per_sqft_values = _collect_price_per_sqft(listings)
    dom_values = _collect_days_on_market(listings)

    stale_threshold = OverallSalesMetrics.model_fields["stale_threshold_days"].default
    fresh_threshold = OverallSalesMetrics.model_fields["fresh_threshold_days"].default

    overall = OverallSalesMetrics(
        listing_count=len(listings),
        median_price=_median(prices),
        mean_price=_mean(prices),
        min_price=_min_value(prices),
        max_price=_max_value(prices),
        p25_price=_percentile(prices, 0.25),
        p75_price=_percentile(prices, 0.75),
        stddev_price=_stddev(prices),
        median_price_per_sqft=_median(price_per_sqft_values),
        mean_price_per_sqft=_mean(price_per_sqft_values),
        min_price_per_sqft=_min_value(price_per_sqft_values),
        max_price_per_sqft=_max_value(price_per_sqft_values),
        p25_price_per_sqft=_percentile(price_per_sqft_values, 0.25),
        p75_price_per_sqft=_percentile(price_per_sqft_values, 0.75),
        stddev_price_per_sqft=_stddev(price_per_sqft_values),
        median_dom=_median(dom_values),
        mean_dom=_mean(dom_values),
        min_dom=_min_int(dom_values),
        max_dom=_max_int(dom_values),
        p25_dom=_percentile(dom_values, 0.25),
        p75_dom=_percentile(dom_values, 0.75),
        pct_stale_listings=_ratio(
            _count_dom_threshold(dom_values, stale_threshold, "gte"), len(listings)
        ),
        pct_fresh_listings=_ratio(
            _count_dom_threshold(dom_values, fresh_threshold, "lte"), len(listings)
        ),
    )

    price_distribution = PriceDistributionMetrics(
        buckets=_build_buckets(prices)
    )
    price_per_sqft_distribution = PricePerSqftDistributionMetrics(
        buckets=_build_buckets(price_per_sqft_values)
    )

    size_and_age = _build_size_and_age_metrics(listings)
    hoa_metrics = _build_hoa_metrics(listings)
    property_type_metrics = _build_property_type_metrics(listings)
    clusters_by_zip = _build_zip_clusters(listings)
    outliers = _build_outlier_metrics(prices, price_per_sqft_values)

    return SalesMarketMetrics(
        overall=overall,
        price_distribution=price_distribution,
        price_per_sqft_distribution=price_per_sqft_distribution,
        size_and_age=size_and_age,
        hoa=hoa_metrics,
        property_type_metrics=property_type_metrics,
        clusters_by_zip=clusters_by_zip,
        outliers=outliers,
    )


def _collect_prices(listings: List[NormalizedListing]) -> List[float]:
    return [
        listing.pricing.list_price
        for listing in listings
        if listing.pricing.list_price is not None
    ]


def _collect_price_per_sqft(listings: List[NormalizedListing]) -> List[float]:
    values: List[float] = []
    for listing in listings:
        price = listing.pricing.list_price
        sqft = listing.facts.sqft
        if price is None or sqft in (None, 0):
            continue
        values.append(price / sqft)
    return values


def _collect_days_on_market(listings: List[NormalizedListing]) -> List[int]:
    values: List[int] = []
    for listing in listings:
        dom = _compute_days_on_market(listing)
        if dom is not None:
            values.append(dom)
    return values


def _build_buckets(values: Sequence[float], bucket_count: int = 5) -> List[PriceBucket]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if lo == hi:
        return [PriceBucket(bucket_min=lo, bucket_max=hi, count=len(values))]

    step = (hi - lo) / bucket_count
    buckets: List[PriceBucket] = []
    edges = [lo + step * i for i in range(bucket_count)] + [hi]
    for idx in range(bucket_count):
        start = edges[idx]
        end = edges[idx + 1]
        # include upper bound only on last bucket
        count = sum(
            1
            for val in values
            if (val >= start and (val < end or (idx == bucket_count - 1 and val <= end)))
        )
        buckets.append(PriceBucket(bucket_min=start, bucket_max=end, count=count))
    return buckets


def _build_size_and_age_metrics(listings: List[NormalizedListing]) -> SizeAndAgeMetrics:
    sqft_values = [listing.facts.sqft for listing in listings if listing.facts.sqft]
    year_values = [
        listing.facts.year_built for listing in listings if listing.facts.year_built
    ]
    return SizeAndAgeMetrics(
        median_sqft=_median(sqft_values),
        mean_sqft=_mean(sqft_values),
        min_sqft=_min_int(sqft_values),
        max_sqft=_max_int(sqft_values),
        p25_sqft=_percentile(sqft_values, 0.25),
        p75_sqft=_percentile(sqft_values, 0.75),
        median_year_built=_median_int(year_values),
        mean_year_built=_mean(year_values),
        min_year_built=_min_int(year_values),
        max_year_built=_max_int(year_values),
    )


def _build_hoa_metrics(listings: List[NormalizedListing]) -> HoaFeeMetrics:
    hoa_values = [
        listing.hoa.monthly for listing in listings if listing.hoa.monthly is not None
    ]
    return HoaFeeMetrics(
        pct_with_hoa=_ratio(len(hoa_values), len(listings)),
        median_hoa_monthly=_median(hoa_values),
        mean_hoa_monthly=_mean(hoa_values),
        min_hoa_monthly=_min_value(hoa_values),
        max_hoa_monthly=_max_value(hoa_values),
    )


def _build_property_type_metrics(listings: List[NormalizedListing]) -> List[SalesPropertyTypeStats]:
    groups: Dict[str, List[NormalizedListing]] = defaultdict(list)
    for listing in listings:
        key = listing.facts.property_type or "unknown"
        groups[key].append(listing)
    total = len(listings)
    stats: List[SalesPropertyTypeStats] = []
    for property_type, entries in sorted(groups.items()):
        prices = [
            e.pricing.list_price for e in entries if e.pricing.list_price is not None
        ]
        price_per_sqft = [
            e.pricing.list_price / e.facts.sqft
            for e in entries
            if e.pricing.list_price is not None and e.facts.sqft not in (None, 0)
        ]
        sqft_values = [e.facts.sqft for e in entries if e.facts.sqft]
        year_values = [
            e.facts.year_built for e in entries if e.facts.year_built is not None
        ]
        dom_values: List[int] = []
        for entry in entries:
            dom = _compute_days_on_market(entry)
            if dom is not None:
                dom_values.append(dom)
        stats.append(
            SalesPropertyTypeStats(
                property_type=property_type,
                count=len(entries),
                pct_of_inventory=_ratio(len(entries), total),
                median_price=_median(prices),
                median_price_per_sqft=_median(price_per_sqft),
                median_sqft=_median(sqft_values),
                median_year_built=_median_int(year_values),
                median_dom=_median(dom_values),
            )
        )
    return stats


def _build_zip_clusters(listings: List[NormalizedListing]) -> List[SalesZipClusterStats]:
    groups: Dict[str, List[NormalizedListing]] = defaultdict(list)
    for listing in listings:
        key = listing.address.zip or "unknown"
        groups[key].append(listing)

    clusters: List[SalesZipClusterStats] = []
    for zip_code, entries in sorted(groups.items()):
        prices = [
            e.pricing.list_price for e in entries if e.pricing.list_price is not None
        ]
        price_per_sqft = [
            e.pricing.list_price / e.facts.sqft
            for e in entries
            if e.pricing.list_price is not None and e.facts.sqft not in (None, 0)
        ]
        sqft_values = [e.facts.sqft for e in entries if e.facts.sqft]
        dom_values: List[int] = []
        for entry in entries:
            dom = _compute_days_on_market(entry)
            if dom is not None:
                dom_values.append(dom)
        year_values = [
            e.facts.year_built for e in entries if e.facts.year_built is not None
        ]

        lat_values = [e.address.lat for e in entries if e.address.lat is not None]
        lon_values = [e.address.lon for e in entries if e.address.lon is not None]

        clusters.append(
            SalesZipClusterStats(
                zip=zip_code,
                count=len(entries),
                median_price=_median(prices),
                median_price_per_sqft=_median(price_per_sqft),
                median_sqft=_median(sqft_values),
                median_dom=_median(dom_values),
                median_year_built=_median_int(year_values),
                centroid_lat=_mean(lat_values),
                centroid_lon=_mean(lon_values),
            )
        )
    return clusters


def _build_outlier_metrics(prices: Sequence[float], price_per_sqft: Sequence[float]) -> SalesOutlierMetrics:
    low_price, high_price = _iqr_bounds(prices)
    low_ppsf, high_ppsf = _iqr_bounds(price_per_sqft)

    return SalesOutlierMetrics(
        low_price_outlier_count=_count_outliers(prices, low_price, True),
        high_price_outlier_count=_count_outliers(prices, high_price, False),
        low_price_per_sqft_outlier_count=_count_outliers(price_per_sqft, low_ppsf, True),
        high_price_per_sqft_outlier_count=_count_outliers(price_per_sqft, high_ppsf, False),
    )


def _iqr_bounds(values: Sequence[float]) -> tuple[Optional[float], Optional[float]]:
    if len(values) < 4:
        return (None, None)
    q1 = _percentile(values, 0.25)
    q3 = _percentile(values, 0.75)
    if q1 is None or q3 is None:
        return (None, None)
    iqr = q3 - q1
    return (q1 - 1.5 * iqr, q3 + 1.5 * iqr)


def _count_outliers(values: Sequence[float], bound: Optional[float], is_low: bool) -> int:
    if bound is None:
        return 0
    if is_low:
        return sum(1 for val in values if val < bound)
    return sum(1 for val in values if val > bound)


def _compute_days_on_market(listing: NormalizedListing) -> Optional[int]:
    listed = _parse_date(listing.dates.listed)
    end = _parse_date(listing.dates.removed) or _parse_date(listing.dates.last_seen)
    if listed is None or end is None:
        return None
    delta = (end - listed).days
    if delta < 0:
        return None
    return delta


def _parse_date(value: Optional[str]):
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


def _mean(values: Sequence[float]) -> Optional[float]:
    return mean(values) if values else None


def _median(values: Sequence[float]) -> Optional[float]:
    return median(values) if values else None


def _median_int(values: Sequence[int]) -> Optional[int]:
    med = _median(values)
    if med is None:
        return None
    return int(round(med))


def _min_value(values: Sequence[float]) -> Optional[float]:
    return min(values) if values else None


def _max_value(values: Sequence[float]) -> Optional[float]:
    return max(values) if values else None


def _min_int(values: Sequence[int]) -> Optional[int]:
    return int(min(values)) if values else None


def _max_int(values: Sequence[int]) -> Optional[int]:
    return int(max(values)) if values else None


def _stddev(values: Sequence[float]) -> Optional[float]:
    return pstdev(values) if len(values) > 1 else None


def _percentile(values: Sequence[float], pct: float) -> Optional[float]:
    if not values:
        return None
    sorted_vals = sorted(values)
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = (len(sorted_vals) - 1) * pct
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return sorted_vals[int(rank)]
    lower_val = sorted_vals[lower]
    upper_val = sorted_vals[upper]
    return lower_val * (upper - rank) + upper_val * (rank - lower)


def _ratio(count: int, total: int) -> Optional[float]:
    if total <= 0:
        return None
    return count / total


def _count_dom_threshold(values: Sequence[int], threshold: int, mode: str) -> int:
    if mode == "gte":
        return sum(1 for v in values if v >= threshold)
    return sum(1 for v in values if v <= threshold)
