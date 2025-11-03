"""Background worker to release expired order reservations."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict

from ..core.config import get_settings
from ..db.session import get_db_session
from ..repositories import orders as order_repo

logger = logging.getLogger(__name__)


@contextmanager
def _session_scope(database_url: str):
    iterator = get_db_session(database_url)
    session = next(iterator)
    try:
        yield session
    finally:
        try:
            next(iterator)
        except StopIteration:
            pass


def handle(event: Dict[str, Any], _context: Any | None = None) -> Dict[str, Any]:
    """Expire stale reservations and release inventory holds."""

    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to sweep reservations")

    expired_total = 0
    sweep_time = datetime.now(timezone.utc)

    with _session_scope(settings.database_url) as session:
        expired_total = order_repo.expire_stale_reservations(session, now=sweep_time)

    logger.info(
        "Reservation sweep complete",
        extra={"expired": expired_total, "timestamp": sweep_time.isoformat()},
    )
    return {"expired": expired_total}
