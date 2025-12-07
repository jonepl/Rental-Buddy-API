from __future__ import annotations

from pytest import approx

from app.domain.dto import Address, Dates, Facts, NormalizedListing, Pricing
from app.domain.regional_metrics import compute_regional_metrics


def _make_listing(
    *,
    listing_id: str,
    rent: float | None,
    sqft: int | None,
    property_type: str | None,
    zip_code: str | None,
    distance: float | None,
    lat: float | None = None,
    lon: float | None = None,
    listed: str | None = None,
    removed: str | None = None,
    last_seen: str | None = None,
) -> NormalizedListing:
    return NormalizedListing(
        id=listing_id,
        category="rental",
        address=Address(zip=zip_code, lat=lat, lon=lon),
        facts=Facts(sqft=sqft, property_type=property_type),
        pricing=Pricing(list_price=rent),
        dates=Dates(listed=listed, removed=removed, last_seen=last_seen),
        distance_miles=distance,
    )


def test_compute_regional_metrics_basic() -> None:
    rentals = [
        _make_listing(
            listing_id="l1",
            rent=2000,
            sqft=1000,
            property_type="single_family",
            zip_code="12345",
            distance=1.0,
            listed="2024-01-01",
            removed="2024-01-11",
        ),
        _make_listing(
            listing_id="l2",
            rent=2400,
            sqft=1200,
            property_type="single_family",
            zip_code="12345",
            distance=2.0,
            listed="2024-01-05",
            last_seen="2024-01-25",
        ),
        _make_listing(
            listing_id="l3",
            rent=1800,
            sqft=900,
            property_type="condo",
            zip_code="67890",
            distance=None,
            lat=30.0,
            lon=-97.0,
            listed="2024-02-10",
            last_seen="2024-02-15",
        ),
        _make_listing(
            listing_id="l4",
            rent=None,
            sqft=800,
            property_type=None,
            zip_code=None,
            distance=None,
            listed=None,
        ),
    ]

    metrics = compute_regional_metrics(rentals, center_lat=30.0, center_lon=-97.0)

    assert metrics.overall.count == 4
    assert metrics.overall.min_rent == 1800
    assert metrics.overall.max_rent == 2400
    assert metrics.overall.mean_rent == approx(2066.6667, rel=1e-4)
    assert metrics.overall.median_rent == 2000
    assert metrics.overall.p25_rent == 1900
    assert metrics.overall.p75_rent == 2200

    assert metrics.overall.min_rent_per_sqft == 2.0
    assert metrics.overall.max_rent_per_sqft == 2.0
    assert metrics.overall.mean_rent_per_sqft == 2.0
    assert metrics.overall.median_rent_per_sqft == 2.0

    assert metrics.overall.mean_days_on_market == approx(11.6667, rel=1e-4)
    assert metrics.overall.median_days_on_market == 10
    assert metrics.overall.fastest_days_on_market == 5
    assert metrics.overall.slowest_days_on_market == 20

    assert metrics.distance.median_distance_miles == 1.0
    assert metrics.distance.rent_distance_correlation == approx(0.9819805, rel=1e-6)
    assert metrics.distance.distance_weighted_median_rent == 1800

    prop_types = {stat.property_type: stat for stat in metrics.property_type_metrics}
    assert prop_types["single_family"].count == 2
    assert prop_types["single_family"].median_rent == 2200
    assert prop_types["single_family"].median_sqft == 1100
    assert prop_types["single_family"].mean_days_on_market == 15

    assert prop_types["condo"].count == 1
    assert prop_types["condo"].median_rent == 1800
    assert prop_types["condo"].median_rent_per_sqft == 2.0

    assert prop_types["unknown"].count == 1
    assert prop_types["unknown"].median_rent is None
    assert prop_types["unknown"].median_sqft == 800

    clusters = {cluster.cluster_key: cluster for cluster in metrics.clusters_by_zip}
    assert clusters["12345"].count == 2
    assert clusters["12345"].median_rent == 2200
    assert clusters["67890"].median_rent_per_sqft == 2.0
    assert clusters["unknown"].median_rent is None


def test_compute_regional_metrics_handles_empty_input() -> None:
    metrics = compute_regional_metrics([], center_lat=None, center_lon=None)

    assert metrics.overall.count == 0
    assert metrics.overall.mean_rent is None
    assert metrics.distance.median_distance_miles is None
    assert metrics.property_type_metrics == []
    assert metrics.clusters_by_zip == []
