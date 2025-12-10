from __future__ import annotations

from app.domain.dto.listings import (Address, Dates, Facts, NormalizedListing,
                                     Pricing)
from app.domain.sales_metrics import compute_sales_metrics


def _listing(
    listing_id: str,
    price: float,
    sqft: int,
    *,
    property_type: str,
    zip_code: str,
    lat: float | None = None,
    lon: float | None = None,
    listed: str = "2024-01-01",
    last_seen: str = "2024-01-15",
    year_built: int | None = 2000,
    hoa: float | None = None,
) -> NormalizedListing:
    listing = NormalizedListing(
        id=listing_id,
        category="sale",
        address=Address(zip=zip_code, lat=lat, lon=lon),
        facts=Facts(property_type=property_type, sqft=sqft, year_built=year_built),
        pricing=Pricing(list_price=price),
        dates=Dates(listed=listed, last_seen=last_seen),
    )
    if hoa is not None:
        listing.hoa.monthly = hoa
    return listing


def test_compute_sales_metrics_basic():
    listings = [
        _listing(
            "s1",
            price=300000,
            sqft=1500,
            property_type="single_family",
            zip_code="12345",
            lat=30.0,
            lon=-97.0,
            hoa=100,
        ),
        _listing(
            "s2",
            price=360000,
            sqft=1200,
            property_type="condo",
            zip_code="67890",
            lat=30.1,
            lon=-97.1,
            listed="2024-02-01",
            last_seen="2024-02-20",
        ),
        _listing(
            "s3",
            price=380000,
            sqft=1800,
            property_type="single_family",
            zip_code="12345",
            lat=30.05,
            lon=-97.05,
            year_built=2010,
        ),
    ]

    metrics = compute_sales_metrics(listings)

    assert metrics.overall.listing_count == 3
    assert metrics.overall.min_price == 300000
    assert metrics.overall.max_price == 380000
    assert metrics.overall.median_price == 360000
    assert metrics.overall.median_price_per_sqft is not None
    assert metrics.price_distribution.buckets
    assert metrics.price_per_sqft_distribution.buckets

    assert metrics.size_and_age.median_sqft == 1500
    assert metrics.size_and_age.median_year_built == 2000
    assert metrics.hoa.pct_with_hoa == 1 / 3

    prop_stats = {stat.property_type: stat for stat in metrics.property_type_metrics}
    assert prop_stats["single_family"].count == 2
    assert prop_stats["condo"].median_price == 360000

    clusters = {cluster.zip: cluster for cluster in metrics.clusters_by_zip}
    assert clusters["12345"].count == 2
    assert clusters["12345"].median_price == 340000
    assert clusters["12345"].centroid_lat is not None

    assert metrics.outliers.low_price_outlier_count >= 0
