from __future__ import annotations

from typing import Any, Dict

from app.domain.dto import ErrorDetail, ErrorEnvelope


def err(code: str, message: str, details: Dict[str, Any] | None = None) -> ErrorEnvelope:
    return ErrorEnvelope(error=ErrorDetail(code=code, message=message, details=details or {}))
