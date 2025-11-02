"""Shared helpers for API route modules."""

from __future__ import annotations

import uuid
from typing import Dict

from fastapi import HTTPException

from ...schemas.common import ErrorResponse


def not_implemented(endpoint: str) -> HTTPException:
    """Return a standardized HTTP 501 response."""

    error = ErrorResponse(
        code="not_implemented",
        message=f"{endpoint} contract not implemented yet",
        details={"request_id": str(uuid.uuid4())},
    )
    return HTTPException(status_code=501, detail=error.dict())


def build_request_metadata(request_id: str | None = None) -> Dict[str, str]:
    """Generate request metadata payload."""

    return {"request_id": request_id or str(uuid.uuid4())}
