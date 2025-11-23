# Rental Buddy API

Rental Buddy is a FastAPI service that provides normalized rental and sales listing data by orchestrating multiple providers through a Hexagonal Architecture. Each port (RentCast, OpenCage, cache, pagination) is implemented as an adapter so the core domain and application services stay provider-agnostic.

## Overview

- **Domain-first design** – Request/response DTOs, ports, and business rules live under `app/domain`.
- **Application services** – `ListingsService` and `GeocodingService` orchestrate domain logic and call ports.
- **Adapters** – RentCast and OpenCage providers implement the port contracts (`app/providers/**`), while FastAPI routes/presenters act as the driving adapters.
- **Shared presenter** – `app/api/presenters/listings_presenter.py` renders the canonical `ListingsResponse` envelope for both `/sales` and `/rentals`.
- **Extensive tests** – Unit tests for adapters, services, presenters, plus integration tests for the HTTP layer.

## Features

- 🔄 Unified `/api/v1/sales` and `/api/v1/rentals` endpoints powered by the same application services
- 🌐 Address, city/state, zip, or lat/lon search input with geocoding handled via an injected port
- 🧭 Sorting, pagination, and filter summaries handled in the domain layer
- 💾 Cache + telemetry metadata in every response envelope
- 📑 Hex-friendly wiring through dependency overrides (great for testing/mocking)
- 🐳 Docker-ready, with typed Pydantic models and structured provider error handling

## Quick Start

### Prerequisites

- Python 3.11+
- OpenCage API key ([get one here](https://opencagedata.com/dashboard#geocoding))
- RentCast API key ([get one here](https://app.rentcast.io/app/api))

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rental-buddy
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv       # On Windows usepy -3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the application:
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Usage

### Rentals

**POST** `/api/v1/rentals`

```json
{
  "address": "123 Main St, Austin, TX",
  "radius_miles": 5,
  "beds": { "min": 2, "max": 5 },
  "baths": { "min": 1.5 },
  "sort": { "by": "price", "dir": "desc" }
}
```

### Sales

```json
{
  "latitude": 30.26,
  "longitude": -97.74,
  "radius_miles": 10,
  "price": { "max": 600000 },
  "days_old": { "max": 60 },
  "sort": { "by": "beds", "dir": "asc" }
}
```

### Response Envelope (shared presenter)

```json
{
  "input": {
    "center": { "lat": 30.26, "lon": -97.74 },
    "radius_miles": 5,
    "filters": { "beds": 2, "baths": 1.5, "days_old": "1" },
    "location": "123 Main St, Austin, TX"
  },
  "summary": {
    "returned": 50,
    "page": { "limit": 50, "offset": 0, "next_offset": 50 }
  },
  "listings": [
    {
      "id": "prov:rentcast:123",
      "category": "rental",
      "pricing": { "list_price": 2450, "currency": "USD", "period": "monthly" },
      "facts": { "beds": 2, "baths": 2, "sqft": 1182 },
      "address": { "formatted": "123 Main St, Austin, TX 78701" }
    }
  ],
  "meta": {
    "category": "rental",
    "request_id": "rb_2025-11-11T18:25:02Z_abc123",
    "duration_ms": 612,
    "cache": "miss",
    "provider_calls": 1
  }
}
```

### Other Endpoints

- **GET** `/api/v1/health` - Health check
- **GET** `/api/v1/cache/stats` - Cache statistics
- **GET** `/docs` - Interactive API documentation

## Configuration

Environment variables (see `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENCAGE_API_KEY` | ✅ | - | OpenCage geocoding API key |
| `RENTCAST_API_KEY` | ✅ | - | RentCast rental data API key |
| `RENTCAST_RADIUS_MILES_DEFAULT` | ☐ | 5 | Default search radius |
| `RENTCAST_DAYS_OLD_DEFAULT` | ☐ | *:270 | Default listing age filter |
| `REQUEST_TIMEOUT_SECONDS` | ☐ | 12 | HTTP request timeout |
| `MAX_RESULTS` | ☐ | 5 | Maximum comps returned |
| `CACHE_TTL_SECONDS` | ☐ | 600 | Cache time-to-live |
| `LOG_LEVEL` | ☐ | INFO | Logging level |

## Development

### Running Tests

```bash
# All tests
pytest

# Layer-specific
pytest tests/unit/providers
pytest tests/integration/api
```

### Code Quality

```bash
black app tests
isort app tests
ruff check app tests  # if installed
```

### Docker

```bash
# Build image
docker build -t rental-buddy .

# Run container
docker run -p 8000:8000 --env-file .env rental-buddy
```

## Project Structure

```
rental-buddy/
├── app/
│   ├── api/
│   │   ├── routes_*.py              # FastAPI adapters
│   │   └── presenters/              # HTTP presenters (response envelopes)
│   ├── domain/
│   │   ├── dto.py                   # Core DTOs
│   │   └── ports/                   # Listings & geocoding ports
│   ├── providers/
│   │   ├── rentcast/                # Provider adapters (client, mapper, normalizer)
│   │   └── opencage/
│   ├── services/
│   │   ├── listings_service.py      # Application service (domain logic)
│   │   └── geocoding_service.py
│   └── core/, utils/, main.py       # Config, telemetry, app bootstrap
├── tests/
│   ├── unit/                        # Unit tests (domain, services, adapters)
│   └── integration/                 # FastAPI integration tests
├── requirements.txt
├── Dockerfile
└── README.md
```

## Error Handling

The API returns structured error responses:

```json
{
  "code": "400_INVALID_INPUT",
  "message": "Provide either a full US street address or latitude & longitude"
}
```

Error codes:
- `400_INVALID_INPUT` - Invalid request parameters
- `404_NO_RESULTS` - No matching properties found
- `422_VALIDATION_ERROR` - Schema validation failed
- `429_RATE_LIMITED` - Rate limit exceeded
- `502_PROVIDER_UNAVAILABLE` - External API unavailable

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please create a GitHub issue or contact the development team.
