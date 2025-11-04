"""FastAPI application entrypoint for Aleena's Cuisine."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Iterator

from fastapi import FastAPI, Request
from fastapi.responses import Response
from mangum import Mangum

from .api import api_router
from .core.config import get_settings
from .core.logging import (
    configure_logging,
    get_request_context,
    reset_request_context,
    set_request_context,
    update_request_context,
)
from .core.tracing import init_tracing
from .db.session import configure_engine, get_db_session
from .services.catalog_seed import seed_curated_catalog

settings = get_settings()
init_tracing(f"aleenascuisine-{settings.aleena_env}")
configure_logging(settings.log_level)

app = FastAPI(title="Aleena's Cuisine API")

app.include_router(api_router, prefix=settings.api_prefix)


@contextmanager
def _session_scope(database_url: str) -> Iterator:
    session_iter = get_db_session(database_url)
    session = next(session_iter)
    try:
        yield session
    finally:
        try:
            next(session_iter)
        except StopIteration:
            pass


@app.on_event("startup")
def seed_catalog() -> None:
    database_url = settings.database_url or "sqlite:///./aleena_dev.db"
    configure_engine(database_url)
    with _session_scope(database_url) as session:
        inserted, updated = seed_curated_catalog(session)
        if inserted or updated:
            logging.getLogger("app.seed").info(
                "catalog_seed_startup",
                extra={"inserted": inserted, "updated": updated},
            )


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """Attach request context and emit structured request logs."""

    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    path = request.url.path
    order_id = request.path_params.get("order_id")
    customer_id = request.headers.get("x-customer-id")

    token = set_request_context(
        {
            "request_id": request_id,
            "path": path,
            "method": request.method,
            "customer_id": customer_id,
            "order_id": order_id,
        }
    )
    request.state.request_id = request_id

    access_logger = logging.getLogger("app.access")
    response: Response
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        update_request_context(
            duration_ms=duration_ms, status_code=response.status_code
        )
        access_logger.info(
            "request_completed",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["x-request-id"] = request_id
        return response
    except Exception:  # pragma: no cover - defensive logging path
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        update_request_context(duration_ms=duration_ms, status_code=500)
        access_logger.exception(
            "request_failed",
            extra={"status_code": 500, "duration_ms": duration_ms},
        )
        raise
    finally:
        reset_request_context(token)


@app.get("/")
def read_root() -> dict[str, str]:
    context = get_request_context()
    return {
        "message": "Aleena's Cuisine API",
        "api_prefix": settings.api_prefix,
        "request_id": context.get("request_id") or "",
    }


handler = Mangum(app)
