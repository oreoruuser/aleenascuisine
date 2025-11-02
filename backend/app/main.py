"""FastAPI application entrypoint for Aleena's Cuisine."""

from __future__ import annotations

from fastapi import FastAPI
from mangum import Mangum

from .api import api_router
from .core.config import get_settings

settings = get_settings()
app = FastAPI(title="Aleena's Cuisine API")

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Aleena's Cuisine API", "api_prefix": settings.api_prefix}


handler = Mangum(app)
