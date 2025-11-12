# 📄 Product Requirement Document (PRD) – Rental Buddy

## 1. General Information
- **Application Name:** Rental Buddy  
- **Application Type:** REST API  
- **Application Description:** Rental Buddy is a tool that provides rental comparables (“comps”) for a given property to help evaluate investment potential.  

---

## 2. Problem Statement
When purchasing a property with the intention of later renting it out, one of the key factors is understanding the local rental market. Currently, there is no simple tool to provide quick and accurate rental comps for a given address. Homebuyers and investors must manually search across multiple listing platforms.  

Rental Buddy aims to solve this problem by providing an API that returns comparable rental properties near the subject property.  

---

## 3. Proposal
We will build a Python-based API that returns comparable rental listings near a specified location.  

- **Inputs:**  
  - `address` (string, full U.S. street address) — optional; must provide this OR both `latitude` & `longitude`
  - `latitude` (number), `longitude` (number) — optional; must provide both if `address` not provided; if present, skip geocoding
  - `radius_miles` (number) — required
  - `bedrooms` (integer, ≥ 0) — optional
  - `bathrooms` (number, multiple of 0.5; e.g., 1, 1.5, 2) — optional
  - `days_old` (string, default "*:270") — optional

- **Outputs:**  
  - JSON object with:  
    - Input address (string)  
    - List of comps, each containing:  
      - `address`  
      - `price` (USD, integer)  
      - `bedrooms` (integer)  
      - `bathrooms` (integer)  
      - `square_footage` (integer or null)  
      - `distance_miles` (float, rounded to 1 decimal place. tie-break by lower price, then larger sqft)  

3a. Functional & Behavioral Requirements

- Input precedence: If latitude and longitude are provided, use them and skip geocoding; otherwise geocode address.
- Bedrooms/Bathrooms: bedrooms is an integer ≥ 0; bathrooms is a number in 0.5 steps (e.g., 1, 1.5, 2). Filter results by exact bed/bath match.
- Units & rounding: distance_miles in miles, round to 1 decimal; price integer USD; square_footage integer or null.
- Sorting: Sort by distance_miles (asc), then price (asc), then square_footage (desc).
- Search window: Default radius_miles = 5; default recency days_old = "*:270". Both are overridable via request body.
- Data quality: Drop records with missing price or missing coordinates; dedupe by formattedAddress (case-insensitive).
- Provider behavior: For RentCast listings, request limit=50; compute distance via Haversine from the subject point; then filter/sort and return the nearest results.
- Errors: Use structured errors with codes:
  - 400_INVALID_INPUT (bad/missing address+coords, invalid bath step)
  - 404_NO_RESULTS (no matches after filtering)
  - 422_VALIDATION_ERROR (schema validation fail)
  - 429_RATE_LIMITED (throttle/backoff triggered)
  - 502_PROVIDER_UNAVAILABLE (provider 429/5xx after retries)
- Security & ToS: Keys are server-side only; throttle client to ≤ provider limits; exponential backoff on 429/5xx; add a short disclaimer (“informational, not an appraisal”).
- Observability & resilience: Log provider latency/status; include request IDs; small cache (e.g., 5–10 min) keyed by (lat,lng,beds,baths,radius,days_old).
- This keeps your intent near the request/response definition so an AI assistant (or dev) implements the exact behavior before wiring dependencies or writing tests.

### Sample JSON Response
```json
{
  "input": {
    "resolved_address": "123 Main St, Fort Lauderdale, FL 33301",
    "latitude": 26.0052,
    "longitude": -80.2128,
    "bedrooms": 3,
    "bathrooms": 2,
    "radius_miles": 5,
    "days_old": "*:270"
  },
  "comps": [
    {
      "address": "456 Oak Ave, Fort Lauderdale, FL 33301",
      "price": 2400,
      "bedrooms": 3,
      "bathrooms": 2,
      "square_footage": 1400,
      "distance_miles": 0.8
    },
    {
      "address": "789 Pine St, Fort Lauderdale, FL 33301",
      "price": 2300,
      "bedrooms": 3,
      "bathrooms": 2,
      "square_footage": 1350,
      "distance_miles": 1.2
    }
  ]
}
```

### Error Response Example
```json
{
  "code": "400_INVALID_INPUT",
  "message": "Provide either a full US street address or latitude & longitude. Bathrooms must be in 0.5 increments."
}
```

---

## 3b. Updated API Design (Refactor)

This refactor introduces unified listing endpoints for rentals and sales with a normalized DTO and a pure-analytics `/comps` endpoint.

- **Endpoints**
  - `POST /api/v1/rentals` → returns normalized rental listings in a common envelope
  - `POST /api/v1/sales` → returns normalized sale listings in a common envelope
  - `POST /api/v1/comps` → analytics only; accepts listing `ids` from last search or inline normalized `listings`

- **Shared Request Contract (rentals/sales)**
  - Address XOR coordinates. If both are provided, address wins.
  - Fields: `address`, `latitude`, `longitude`, `radius_miles`, `beds`, `baths`, `min_price`, `max_price`, `min_sqft`, `max_sqft`, `days_old`, `limit`, `offset`, `sort: { by, dir }`

- **Response Envelope**
```json
{
  "input": { "center": {"lat": 26.0052, "lon": -80.2128}, "radius_miles": 5.0, "filters": {"beds": 3, "baths": 2.0, "days_old": "*:270"} },
  "summary": { "returned": 50, "count": null, "page": { "limit": 50, "offset": 0, "next_offset": 50 } },
  "listings": [ /* normalized listing */ ],
  "meta": { "category": "rental|sale", "request_id": "rb_...", "duration_ms": 0, "cache": "hit|miss|partial", "provider_calls": 0 }
}
```

- **Normalized Listing DTO (both categories)**
```
{
  "id": "prov:rentcast:abc123",
  "category": "rental|sale",
  "status": "Active",
  "address": { "formatted": "123 Main St, Austin, TX 78701", "line1": "123 Main St", "line2": null, "city": "Austin", "state": "TX", "zip": "78701", "county": "Travis", "county_fips": "48453", "lat": 30.2672, "lon": -97.7431 },
  "facts": { "beds": 3, "baths": 2.0, "sqft": 1400, "year_built": 1984, "property_type": "Single Family Home" },
  "pricing": { "list_price": 2400, "currency": "USD", "period": "monthly|total" },
  "dates": { "listed": "2025-11-01T00:00:00Z", "removed": null, "last_seen": "2025-11-05T14:12:33Z" },
  "hoa": { "monthly": 0 },
  "distance_miles": 1.2,
  "provider": { "name": "rentcast" }
}
```

- **`/comps` (analytics)**
  - Pure CPU. No provider calls. Accepts `ids` (resolved from server cache of last search) or inline `listings`.
  - Computes metrics: price_per_sqft, rent_per_sqft, rent_to_price, gross_yield, cap_rate, grm. Returns `null` when inputs missing.


## 4. External Dependencies
- **OpenCage API Geocoding** – Convert input address → latitude/longitude  
- **RentCast Rental API** – Query rental listings by lat/long, filter by bed/bath, return details  
- **Fallback/Mock** – If APIs are unavailable, return mock JSON with randomized data for testing  

### 4a Config & environment
| Name                            | Required            | Example                  | Notes                                                 |
| ------------------------------- | ------------------- | ------------------------ | ----------------------------------------------------- |
| `OPENCAGE_API_KEY`              | ✅                  | `oc-xxxxxxxx`            | OpenCage Geocoding key. Store in server-side secrets manager; use .env only for local dev |
| `RENTCAST_API_KEY`              | ✅                  | `rc-xxxxxxxx`            | RentCast API key. Store in server-side secrets manager; use .env only for local dev       |
| `RENTCAST_RADIUS_MILES_DEFAULT` | ☐ (default 5)       | `5`                      | Search radius for comps.                              |
| `RENTCAST_DAYS_OLD_DEFAULT`     | ☐ (default `*:270`) | `*:270`                  | Only listings seen in the last N days.                |
| `REQUEST_TIMEOUT_SECONDS`       | ☐ (default 12)      | `12`                     | HTTP client timeout to providers.                     |
| `MAX_RESULTS`                   | ☐ (default 5)       | `5`                      | Cap on returned comps.                                |
| `RATE_LIMIT_RPS`                | ☐ (default 20)      | `20`                     | Safety throttle per key (align with provider limits). |
| `CACHE_TTL_SECONDS`             | ☐ (default 600)     | `600`                    | Optional in-memory cache TTL for identical queries.   |
| `LOG_LEVEL`                     | ☐ (default `INFO`)  | `DEBUG`                  | Service log verbosity.                                |
| `ENVIRONMENT`                   | ☐                   | `dev` / `stage` / `prod` | Enables per-env behavior & keys.                      |


---

## 5. Non-Functional Requirements
- **Performance:** API must return a response within **2 seconds** under typical loads  
- **Scalability:** Support at least **100 concurrent requests**  
- **Reliability:** Must return structured JSON errors for invalid inputs or external API failures  
- **Security:** API keys should be stored securely (e.g., environment variables)  

---

## 6. Testing Requirements
### Test Cases
1. Valid address with bed/bath → returns 5 comps sorted by distance  
2. Invalid address (e.g., "Miami, FL") → returns error JSON  
3. Address with no comps available → returns empty list with no errors  
4. Stress test with 100 concurrent requests → response within 2s

---

## 7. Plan & Project Structure
### Proposed Architecture
- **API Layer:** FastAPI for `/rentals`, `/sales`, and `/comps` endpoints
- Pydantic v2
- httpx
- uvicorn
- **Domain:**  
  - `app/domain/dto.py` → normalized DTOs (requests, envelopes, listing, comps)  
  - `app/domain/analytics.py` → pure analytics (metrics, percentiles, ranks scaffold)  
- **Services:**  
  - `app/services/geocoding_service.py` → geocoding (OpenCage API)   
  - `app/services/property_service.py` → provider access (RentCast)  
  - `app/services/providers/rentcast.py` → adapter mapping provider → normalized listing  
  - `app/services/result_cache.py` → short-lived normalized results cache  
- **Core:**  
  - `app/core/pagination.py` → pagination helpers  
  - `app/core/telemetry.py` → request_id and timings  
  - `app/core/errors.py` → structured error helpers  

### Directory Layout
```
./
  /app
    main.py
    api/
      routes_rentals.py
      routes_sales.py
      routes_comps.py
      endpoints.py              # legacy health/cache (temporarily mounted)
    core/
      config.py
      pagination.py
      telemetry.py
      errors.py
    domain/
      dto.py
      analytics.py
    services/
      geocoding_service.py
      property_service.py
      result_cache.py
      providers/
        rentcast.py
  /tests
    e2e/
      test_comps_endpoint.py
    unit/
      entry/
        test_main.py
        test_api.py
      services/
        test_maps_service.py
        test_property_service.py
  .env
  requirements.txt
  Dockerfile
```

---

## 8. Success Criteria
- `/rentals` and `/sales` return normalized envelopes with `listings` and `distance_miles`  
- `/comps` computes requested derived metrics without provider calls  
- Pagination serves from normalized cache for subsequent pages (no extra provider calls)  
- Consistent JSON snake_case, `null` for unknowns, ISO-8601 UTC timestamps  
- Error envelopes follow structured schema  
- Unit, integration & end-to-end tests passing  

---

## 9. Launch Readiness
- ✅ Code compiles without errors  
- ✅ `/rentals` & `/sales` endpoints respond with normalized envelopes  
- ✅ `/comps` endpoint returns analytics for inline items (IDs via cache supported)  
- ✅ Unit & integration tests green  
- ✅ End-to-end tests green  
- ✅ OpenAPI/Swagger documentation generated  
- ✅ Ready for Docker deployment
- ✅ Swagger JSON validated
- ✅ Secrets scan passes (no keys in repo).

---

## 11. Future Enhancements

- **Pagination from cache across requests**  
  - Surface and accept a `request_id` to page the previously cached normalized result set without re-calling providers.
- **Meta accuracy and telemetry**  
  - Propagate `request_id`, compute precise `duration_ms`, and mark `cache` as hit/miss/partial with accurate `provider_calls`.
- **Group summaries and ranking in `/comps`**  
  - Add percentiles and ranks (e.g., P50/P90, pct ranks), with optional `group_by` aggregations.
- **Timestamp normalization**  
  - Ensure all provider timestamps are normalized to ISO-8601 with `Z` suffix.
- **Dedupe refinements**  
  - Improve proximity dedupe threshold, tie-break by `dates.last_seen` (keep newest).
- **Health and cache endpoints**  
  - Move `/health` and `/cache/stats` to a small dedicated router; remove legacy router.
- **Provider adapter coverage**  
  - Map any remaining RentCast fields and ignore unknowns safely.
- **Validation**  
  - Harden numeric coercion and explicit rejects for non-numeric placeholders (e.g., "N/A").
- **Testing**  
  - Add DTO validation tests (address XOR lat/lon; baths step; bounds), analytics golden tests, provider mapping tests, and e2e search→comps flow.

---

## 10. Reviewer Checklist
- Does everyone understand what we are building?  
- Have we validated inputs/outputs with mock data?  
- Do we know how to measure success (accuracy, response time, error handling)?  
- Do we have a fallback plan if external APIs are unavailable?  



#### Notes

# OpenCage Geocoder
https://opencagedata.com/dashboard#geocoding

# RentCast
https://app.rentcast.io/app/api

Best first candidate: RentCast — because it provides rental listings, comps, valuations, and has a free tier. It likely covers most of what you need for the POC.

Fallbacks / augment with: Rentometer (for rent-specific comps), HelloData; or combine property attribute providers like Estated + public MLS / listing sources.
