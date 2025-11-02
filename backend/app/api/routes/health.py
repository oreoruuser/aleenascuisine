"""Health and readiness endpoints."""

from __future__ import annotations

import uuid
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..deps import db_session

router = APIRouter(tags=["health"], prefix="")


@router.get("/health", summary="Service health check")
def health_check(session: Session = Depends(db_session)) -> Dict[str, str]:
    """Return a basic health indicator.

    The endpoint intentionally avoids heavy dependencies. Future iterations can
    incorporate database connectivity checks once the data-access layer is ready.
    """
    db_status = "ok"
    try:
        session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - health endpoint resilience
        db_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    return {
        "status": overall,
        "database": db_status,
        "request_id": str(uuid.uuid4()),
    }
