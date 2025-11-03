"""FastAPI application entrypoint for Aleena's Cuisine."""

from __future__ import annotations

import logging
import time
import uuid

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

settings = get_settings()
init_tracing(f"aleenascuisine-{settings.aleena_env}")
configure_logging(settings.log_level)

app = FastAPI(title="Aleena's Cuisine API")

app.include_router(api_router, prefix=settings.api_prefix)


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
