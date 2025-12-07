# 📘 Regional Rental Metrics Engine — Design Specification
### Rental Buddy Backend — Domain Service Proposal

## 1. Overview
Rental Buddy needs a way to estimate **rental comps regionally** without hitting RentCast’s “comps per property” endpoint for every single listing.  
The solution is a **Regional Rental Metrics Engine**, computed from a single RentCast rental search using the same filters as the user’s for-sale search.

The backend returns sales listings via `ListingsResponse`, which uses `NormalizedListing` objects. Rental listings retrieved through the RentCast adapter also use the same DTO structure.

This metrics engine will compute:

- rental market statistics  
- rent/sqft and rent/bedroom calculations  
- geographic weighting  
- property-type normalization  
- zip-code clustering  

These metrics power a **best-guess rent estimate** for each for-sale property *without* exceeding rate limits.

## 2. Input Data Shape

The metrics engine consumes **rental listings only**, returned in the form of:

```
ListingsResponse   # category="rental"
```

Each rental listing is a `NormalizedListing` with the following relevant fields:

- `address.lat`, `address.lon`, `address.zip`
- `facts.beds`, `facts.baths`, `facts.sqft`, `facts.property_type`
- `pricing.list_price` (monthly rent for rental listings)
- `dates.listed`
- `distance_miles` (optional)

The engine extracts:

```
rent = listing.pricing.list_price
beds = listing.facts.beds
baths = listing.facts.baths
sqft = listing.facts.sqft
property_type = listing.facts.property_type
lat/lon = listing.address.lat / listing.address.lon
zip = listing.address.zip
days_on_market = derived from listing.dates
```

## 3. Output DTO: RegionalMetrics

```
class RegionalMetrics(BaseModel):
    overall: OverallRentMetrics
    distance: DistanceMetrics
    property_type_metrics: list[PropertyTypeStats]
    clusters_by_zip: list[ClusterRentStats]
```

## 4. Metrics to Implement

### 4.1 Rental Market Metrics (Overall)
Compute:
- min/max/mean/median rent
- 25th/75th percentile rent
- rent per sqft stats
- days-on-market stats (mean, median, fastest, slowest)

### 4.2 Geographic Metrics
Using Haversine distance:
- median distance
- correlation between distance & rent
- distance-weighted median rent
- see app/utils/distance.py for haversine distance calculation

### 4.3 Property Type Metrics
Group by `facts.property_type`:
- count
- median rent
- median rent/sqft
- median sqft
- mean DOM

### 4.4 Zip Code Clusters
Group by `address.zip`:
- cluster count
- median rent
- median rent/sqft

## 5. DTO Definitions

### OverallRentMetrics
```
class OverallRentMetrics(BaseModel):
    count: int
    min_rent: float | None
    max_rent: float | None
    mean_rent: float | None
    median_rent: float | None
    p25_rent: float | None
    p75_rent: float | None

    min_rent_per_sqft: float | None
    max_rent_per_sqft: float | None
    mean_rent_per_sqft: float | None
    median_rent_per_sqft: float | None
    p25_rent_per_sqft: float | None
    p75_rent_per_sqft: float | None

    mean_days_on_market: float | None
    median_days_on_market: float | None
    fastest_days_on_market: int | None
    slowest_days_on_market: int | None
```

### DistanceMetrics
```
class DistanceMetrics(BaseModel):
    median_distance_miles: float | None
    rent_distance_correlation: float | None
    distance_weighted_median_rent: float | None
```

### PropertyTypeStats
```
class PropertyTypeStats(BaseModel):
    property_type: str
    count: int
    median_rent: float | None
    median_rent_per_sqft: float | None
    median_sqft: float | None
    mean_days_on_market: float | None
```

### ClusterRentStats
```
class ClusterRentStats(BaseModel):
    cluster_key: str
    count: int
    median_rent: float | None
    median_rent_per_sqft: float | None
```

## 6. Service Function Contract

```
def compute_regional_metrics(
    rentals: list[NormalizedListing],
    center_lat: float | None,
    center_lon: float | None,
) -> RegionalMetrics:
    ...
```

The function:
- must be pure domain logic  
- must gracefully handle missing values  
- must not perform I/O  

## 7. Backend Integration Flow

1. User searches for **sales listings**
2. Backend performs **secondary rental search** using same search filters
3. Rental results **cached for 12–24 hours**
4. Engine computes `RegionalMetrics`
5. Metrics included in API response or used to compute rent estimates

## 8. Future Extensions

- ML-based rent prediction
- Spatial clustering (k-means)
- Seasonal DOM adjustments
