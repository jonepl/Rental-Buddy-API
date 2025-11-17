from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from app.domain.dto import NormalizedListing, SearchRequest


@runtime_checkable
class ListingsPort(Protocol):
    """
    Domain-level port for fetching property listings from an external provider.

    This is a *pure contract*:
      - It lives in the DOMAIN layer.
      - It knows nothing about HTTP, RentCast, URLs, or API keys.
      - It only deals with domain models: SearchRequest and NormalizedListing.

    Implementations (adapters) will live in providers/, e.g.:
      - app/providers/rentcast/adapter.py -> RentCastAdapter(ListingsPort)
    """

    async def fetch_rentals(
        self,
        request: SearchRequest,
    ) -> List[NormalizedListing]:
        """
        Fetch normalized *rental* listings matching the given search request.

        Notes:
          - Location fields in SearchRequest (lat/lon, address, city/state, zip)
            are interpreted by the adapter implementation.
          - Sorting and pagination are NOT required here; the service layer
            can apply those on top of the returned list.
          - Implementations should raise domain-level provider exceptions
            (e.g., ProviderTimeoutError, ProviderRateLimitError, etc.) on failures.

        Args:
            request: The domain search request (filters, ranges, location, etc.).

        Returns:
            A list of NormalizedListing objects for rental listings.
        """
        ...

    async def fetch_sales(
        self,
        request: SearchRequest,
    ) -> List[NormalizedListing]:
        """
        Fetch normalized *sale* listings matching the given search request.

        Notes:
          - Same behavior contract as fetch_rentals, but for for-sale inventory.
          - Implementations may call different endpoints (e.g., /listings/sale)
            under the hood, but that is invisible to the domain.

        Args:
            request: The domain search request (filters, ranges, location, etc.).

        Returns:
            A list of NormalizedListing objects for sale listings.
        """
        ...
