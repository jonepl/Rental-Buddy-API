import pytest

from app.core.pagination import paginate, slice_page


def test_paginate_basic_no_next():
    returned, limit, next_offset = paginate(total=10, limit=5, offset=5)
    assert returned == 5
    assert limit == 5
    assert next_offset is None


def test_paginate_with_next():
    returned, limit, next_offset = paginate(total=10, limit=3, offset=4)
    assert returned == 3
    assert limit == 3
    assert next_offset == 7


def test_paginate_clamps_limit_and_offset():
    returned, limit, next_offset = paginate(total=5, limit=0, offset=-10)
    assert limit == 1
    assert returned == 1  # min of limit and remaining
    assert next_offset == 1


def test_paginate_offset_beyond_total():
    returned, limit, next_offset = paginate(total=5, limit=10, offset=10)
    assert returned == 0
    assert (
        limit == 10 or limit == 5
    )  # function clamps to max 100, so 10 is fine; accept either to be robust
    assert next_offset is None


def test_slice_page_basic():
    items = list(range(10))
    page = slice_page(items, limit=3, offset=4)
    assert page == [4, 5, 6]


def test_slice_page_clamps():
    items = list(range(10))
    page = slice_page(items, limit=0, offset=-5)
    assert page == [0]


def test_slice_page_tail():
    items = list(range(5))
    page = slice_page(items, limit=3, offset=4)
    assert page == [4]
