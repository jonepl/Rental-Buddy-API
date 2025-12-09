# app/providers/rentcast/adapter.py
from app.core.config import settings
from app.domain.dto.listings import ListingsRequest, NormalizedListing
from app.domain.enums.context_request import OperationType
from app.domain.ports.listings_port import ListingsPort
from app.providers.rentcast.client import RentCastClient
from app.providers.rentcast.mapper import build_params
from app.providers.rentcast.normalizer import normalize_response


class RentCastAdapter(ListingsPort):
    def __init__(self, client: RentCastClient):
        self.client = client
        self.max_results = settings.max_results

    async def fetch_sales(self, request: ListingsRequest) -> list[NormalizedListing]:
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
        params = build_params(request)
        raw = await self.client.get_sales(params)
        listings = normalize_response(raw, OperationType.SALES)
        return listings[: self.max_results]

    async def fetch_rentals(self, request: ListingsRequest) -> list[NormalizedListing]:
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
        params = build_params(request)
        raw = await self.client.get_rentals(params)
        listings = normalize_response(raw, OperationType.RENTALS)
        return listings[: self.max_results]
