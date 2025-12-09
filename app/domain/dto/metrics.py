from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class OverallRentMetrics(BaseModel):
    count: int
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    mean_rent: Optional[float] = None
    median_rent: Optional[float] = None
    p25_rent: Optional[float] = None
    p75_rent: Optional[float] = None

    min_rent_per_sqft: Optional[float] = None
    max_rent_per_sqft: Optional[float] = None
    mean_rent_per_sqft: Optional[float] = None
    median_rent_per_sqft: Optional[float] = None
    p25_rent_per_sqft: Optional[float] = None
    p75_rent_per_sqft: Optional[float] = None

    mean_days_on_market: Optional[float] = None
    median_days_on_market: Optional[float] = None
    fastest_days_on_market: Optional[int] = None
    slowest_days_on_market: Optional[int] = None


class OverallSalesMetrics(BaseModel):
    listing_count: int

    median_price: Optional[float] = None
    mean_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    p25_price: Optional[float] = None
    p75_price: Optional[float] = None
    stddev_price: Optional[float] = None

    median_price_per_sqft: Optional[float] = None
    mean_price_per_sqft: Optional[float] = None
    min_price_per_sqft: Optional[float] = None
    max_price_per_sqft: Optional[float] = None
    p25_price_per_sqft: Optional[float] = None
    p75_price_per_sqft: Optional[float] = None
    stddev_price_per_sqft: Optional[float] = None

    median_dom: Optional[float] = None
    mean_dom: Optional[float] = None
    min_dom: Optional[int] = None
    max_dom: Optional[int] = None
    p25_dom: Optional[float] = None
    p75_dom: Optional[float] = None

    stale_threshold_days: int = 60
    fresh_threshold_days: int = 14
    pct_stale_listings: Optional[float] = None
    pct_fresh_listings: Optional[float] = None


class PriceBucket(BaseModel):
    bucket_min: float
    bucket_max: float
    count: int


class PriceDistributionMetrics(BaseModel):
    buckets: List[PriceBucket] = Field(default_factory=list)


class PricePerSqftDistributionMetrics(BaseModel):
    buckets: List[PriceBucket] = Field(default_factory=list)


class DistanceMetrics(BaseModel):
    median_distance_miles: Optional[float] = None
    rent_distance_correlation: Optional[float] = None
    distance_weighted_median_rent: Optional[float] = None


class PropertyTypeStats(BaseModel):
    property_type: str
    count: int
    median_rent: Optional[float] = None
    median_rent_per_sqft: Optional[float] = None
    median_sqft: Optional[float] = None
    mean_days_on_market: Optional[float] = None


class ClusterRentStats(BaseModel):
    cluster_key: str
    count: int
    median_rent: Optional[float] = None
    median_rent_per_sqft: Optional[float] = None


class RentalMarketMetrics(BaseModel):
    overall: OverallRentMetrics
    distance: DistanceMetrics
    property_type_metrics: List[PropertyTypeStats]
    clusters_by_zip: List[ClusterRentStats]


class SizeAndAgeMetrics(BaseModel):
    median_sqft: Optional[float] = None
    mean_sqft: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    p25_sqft: Optional[float] = None
    p75_sqft: Optional[float] = None

    median_year_built: Optional[int] = None
    mean_year_built: Optional[float] = None
    min_year_built: Optional[int] = None
    max_year_built: Optional[int] = None


class SalesPropertyTypeStats(BaseModel):
    property_type: str
    count: int
    pct_of_inventory: Optional[float] = None
    median_price: Optional[float] = None
    median_price_per_sqft: Optional[float] = None
    median_sqft: Optional[float] = None
    median_year_built: Optional[int] = None
    median_dom: Optional[float] = None


class HoaFeeMetrics(BaseModel):
    pct_with_hoa: Optional[float] = None
    median_hoa_monthly: Optional[float] = None
    mean_hoa_monthly: Optional[float] = None
    min_hoa_monthly: Optional[float] = None
    max_hoa_monthly: Optional[float] = None


class SalesZipClusterStats(BaseModel):
    zip: str
    count: int
    median_price: Optional[float] = None
    median_price_per_sqft: Optional[float] = None
    median_sqft: Optional[float] = None
    median_dom: Optional[float] = None
    median_year_built: Optional[int] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None


class SalesOutlierMetrics(BaseModel):
    low_price_outlier_count: int = 0
    high_price_outlier_count: int = 0
    low_price_per_sqft_outlier_count: int = 0
    high_price_per_sqft_outlier_count: int = 0


class SalesMarketMetrics(BaseModel):
    overall: OverallSalesMetrics
    price_distribution: PriceDistributionMetrics
    price_per_sqft_distribution: PricePerSqftDistributionMetrics
    size_and_age: SizeAndAgeMetrics
    hoa: HoaFeeMetrics
    property_type_metrics: List[SalesPropertyTypeStats]
    clusters_by_zip: List[SalesZipClusterStats]
    outliers: SalesOutlierMetrics


class PropertyInvestmentMetrics(BaseModel):
    market_rent_monthly: Optional[float] = None
    rent_low: Optional[float] = None
    rent_high: Optional[float] = None
    rent_per_sqft: Optional[float] = None
    rent_per_bedroom: Optional[float] = None
    rent_range_spread_pct: Optional[float] = None

    purchase_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    rv_ratio_monthly: Optional[float] = None
    gross_yield: Optional[float] = None
    grm: Optional[float] = None
    delta_vs_area_median_price_pct: Optional[float] = None

    noi_annual: Optional[float] = None
    cap_rate: Optional[float] = None
    expense_ratio: Optional[float] = None

    loan_amount_std: Optional[float] = None
    monthly_pi_std: Optional[float] = None
    dscr_std: Optional[float] = None
    monthly_cashflow_std: Optional[float] = None
    cash_on_cash_std: Optional[float] = None

    rent_uncertainty_score: Optional[float] = None
    comp_density_score: Optional[float] = None
    price_dispersion_score: Optional[float] = None


class PropertyInvestmentScore(BaseModel):
    overall_score: float
    cashflow_score: float
    value_score: float
    risk_score: float
    metrics: PropertyInvestmentMetrics
