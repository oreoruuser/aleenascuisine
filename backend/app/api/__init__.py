"""API router configuration for Aleena's Cuisine."""

from __future__ import annotations

from fastapi import APIRouter

from .routes import admin, cakes, cart, health, orders

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(cakes.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(orders.payments_router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
