import pytest
from pydantic import ValidationError

from app.domain.range_types import Range


def test_range_creation():
    # Test basic creation with min and max
    r = Range[int](min=1, max=5)
    assert r.min == 1
    assert r.max == 5
    assert not r.is_point

    # Test creation with just min
    r = Range[int](min=1)
    assert r.min == 1
    assert r.max is None

    # Test creation with just max
    r = Range[int](max=5)
    assert r.min is None
    assert r.max == 5

    # Test creation with float values
    r = Range[float](min=1.5, max=2.5)
    assert r.min == 1.5
    assert r.max == 2.5


def test_to_provider():
    # Test with both min and max
    r = Range[int](min=1, max=5)
    assert r.to_provider() == "1:5"

    # Test with just min
    r = Range[int](min=1)
    assert r.to_provider() == "1:*"

    # Test with just max
    r = Range[int](max=5)
    assert r.to_provider() == "*:5"

    # Test with float values
    r = Range[float](min=1.5, max=2.5)
    assert r.to_provider() == "1.5:2.5"

    # Test with no bounds (shouldn't normally happen but good to test)
    r = Range[int]()
    assert r.to_provider() == "*:*"


def test_is_point():
    # Test with point range
    r = Range[int](min=5, max=5)
    assert r.is_point

    # Test with different min/max
    r = Range[int](min=1, max=5)
    assert not r.is_point

    # Test with missing min
    r = Range[int](max=5)
    assert not r.is_point

    # Test with missing max
    r = Range[int](min=5)
    assert not r.is_point


def test_validation():
    # Test extra fields are not allowed
    with pytest.raises(ValidationError):
        Range[int](min=1, max=5, extra_field=10)

    # Test type validation
    with pytest.raises(ValidationError):
        Range[int](min="not an int")

    # Test float range with int values (should be fine)
    r = Range[float](min=1, max=5)  # ints are valid for float Range
    assert r.min == 1.0  # Note: Pydantic will convert to float
    assert r.max == 5.0


def test_equality():
    r1 = Range[int](min=1, max=5)
    r2 = Range[int](min=1, max=5)
    r3 = Range[int](min=2, max=5)

    assert r1 == r2
    assert r1 != r3
    assert r1 != "not a range"  # type: ignore[comparison-overlap]
