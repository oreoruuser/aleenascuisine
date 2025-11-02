"""Schemas for administrative cake management operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import RequestMetadata


class CakeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str]
    price: float = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    category: Optional[str]
    is_available: bool = Field(
        True, description="Whether the cake is currently sellable"
    )
    stock_quantity: int = Field(..., ge=0)
    image_url: Optional[str]


class CakeUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    category: Optional[str] = None
    is_available: Optional[bool] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None


class CakeAvailabilityRequest(BaseModel):
    is_available: bool
    reason: Optional[str] = Field(None, max_length=512)


class InventoryAdjustmentRequest(BaseModel):
    delta: int = Field(
        ..., description="Positive to increase inventory, negative to decrease"
    )
    reason: Optional[str] = Field(None, max_length=512)


class AdminActionResponse(BaseModel):
    success: bool
    request: RequestMetadata


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New order status")
