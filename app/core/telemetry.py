from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from typing import Iterator, Tuple


def request_id() -> str:
    return f"rb_{time.strftime('%Y-%m-%dT%H:%M:%SZ')}_{uuid.uuid4().hex[:6]}"


@contextmanager
def timer() -> Iterator[Tuple[float, int]]:
    start = time.perf_counter()
    yield start, 0
    # context manager doesn't automatically compute; leave to caller if needed


def duration_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
