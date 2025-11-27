from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", int, float)


class Range(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    min: Optional[T] = None
    max: Optional[T] = None

    @property
    def is_point(self) -> bool:
        return self.min is not None and self.max is not None and self.min == self.max

    def to_provider(self) -> str:
        left = "*" if self.min is None else str(self.min)
        right = "*" if self.max is None else str(self.max)
        return f"{left}:{right}"
