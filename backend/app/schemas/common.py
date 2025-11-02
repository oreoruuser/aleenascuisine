"""Common data models shared across API schemas."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., description="Stable application error code")
    message: str = Field(..., description="Human readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Optional structured details about the failure"
    )


class RequestMetadata(BaseModel):
    request_id: str = Field(..., description="Server generated request correlation id")
