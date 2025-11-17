from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.domain.dto import NormalizedListing


@dataclass
class CachedSearch:
    created: float
    center_lat: float
    center_lon: float
    category: str
    listings: List[NormalizedListing] = field(default_factory=list)
    by_id: Dict[str, NormalizedListing] = field(default_factory=dict)


class ResultCache:
    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._searches: Dict[str, CachedSearch] = {}

    def put(
        self,
        key: str,
        center_lat: float,
        center_lon: float,
        category: str,
        listings: List[NormalizedListing],
    ):
        now = time.time()
        cs = CachedSearch(
            created=now,
            center_lat=center_lat,
            center_lon=center_lon,
            category=category,
            listings=listings,
        )
        cs.by_id = {x.id: x for x in listings}
        self._searches[key] = cs

    def get_ids(self, key: str) -> Optional[List[str]]:
        cs = self._get_valid(key)
        if not cs:
            return None
        return [x.id for x in cs.listings]

    def get_listing(self, key: str, id_: str) -> Optional[NormalizedListing]:
        cs = self._get_valid(key)
        if not cs:
            return None
        return cs.by_id.get(id_)

    def get_all(self, key: str) -> Optional[List[NormalizedListing]]:
        cs = self._get_valid(key)
        if not cs:
            return None
        return cs.listings

    def _get_valid(self, key: str) -> Optional[CachedSearch]:
        cs = self._searches.get(key)
        if not cs:
            return None
        if (time.time() - cs.created) > self._ttl:
            self._searches.pop(key, None)
            return None
        return cs


# Shared singleton for app modules
result_cache = ResultCache(ttl_seconds=300)
