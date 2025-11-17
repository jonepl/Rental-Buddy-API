import re
from unittest.mock import MagicMock, patch

from app.core.telemetry import duration_ms, request_id, timer


def test_request_id_format_and_uniqueness():
    with patch("time.strftime", return_value="2025-01-01T00:00:00Z"):
        # Mock uuid objects with controlled hex values
        u1 = MagicMock()
        u1.hex = "abcdef1234567890"
        u2 = MagicMock()
        u2.hex = "123456abcdef7890"
        with patch("uuid.uuid4", side_effect=[u1, u2]):
            rid1 = request_id()
            rid2 = request_id()
    # Expected format rb_<iso>_<6hex>
    assert rid1.startswith("rb_2025-01-01T00:00:00Z_")
    assert rid2.startswith("rb_2025-01-01T00:00:00Z_")
    # last 6 chars come from the mocked uuid hex
    assert rid1.endswith("abcdef")
    assert rid2.endswith("123456")
    assert rid1 != rid2
    assert re.fullmatch(r"rb_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z_[0-9a-f]{6}", rid1)


def test_timer_yields_start_and_zero():
    with patch("time.perf_counter", return_value=123.456):
        with timer() as (start, zero):
            assert start == 123.456
            assert zero == 0


def test_duration_ms_deterministic():
    # Start time provided as arg; mock perf_counter to simulate now
    with patch("time.perf_counter", return_value=100.456):
        ms = duration_ms(100.000)
    assert ms == 456
