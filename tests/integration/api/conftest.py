from __future__ import annotations

from typing import Callable, List, Optional

import pytest

from app.domain.dto import ListingsRequest, NormalizedListing
from tests.integration.api.helpers import StubListingsService
from tests.integration.api.helpers import make_listing as build_listing


@pytest.fixture
def make_listing() -> Callable[..., NormalizedListing]:
    """
    Fixture returning the shared helper for building NormalizedListing objects.
    """
    return build_listing


@pytest.fixture
def stub_listings_service_factory() -> (
    Callable[[Optional[List[NormalizedListing]], Exception | None], StubListingsService]
):
    """
    Fixture that returns a factory for creating StubListingsService instances.
    """

    def _factory(
        listings: Optional[List[NormalizedListing]] = None,
        error: Exception | None = None,
    ) -> StubListingsService:
        return StubListingsService(listings=listings, error=error)

    return _factory
