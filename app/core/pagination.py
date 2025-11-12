from __future__ import annotations

from typing import List, Tuple


def paginate(total: int, limit: int, offset: int) -> Tuple[int, int, int | None]:
    limit = max(1, min(100, limit))
    offset = max(0, offset)
    returned = max(0, min(limit, max(0, total - offset)))
    next_offset = offset + returned if (offset + returned) < total else None
    return returned, limit, next_offset


def slice_page(items: List, limit: int, offset: int) -> List:
    limit = max(1, min(100, limit))
    offset = max(0, offset)
    return items[offset : offset + limit]
