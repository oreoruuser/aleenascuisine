"""Cart request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import RequestMetadata


class CartItemInput(BaseModel):
    cake_id: str
    quantity: int = Field(..., gt=0)
    price_each: float = Field(..., ge=0)


class CartUpsertRequest(BaseModel):
    customer_id: Optional[str] = Field(
        None, description="Customer UUID associated with the cart"
    )
    cart_token: Optional[str] = Field(
        None, description="Ephemeral token used for guest checkout"
    )
    items: List[CartItemInput] = Field(..., min_length=1)


class MoneyBreakdown(BaseModel):
    subtotal: float = Field(..., ge=0)
    taxes: float = Field(..., ge=0)
    shipping: float = Field(..., ge=0)
    total: float = Field(..., ge=0)


class CartItem(BaseModel):
    cart_item_id: str
    cake_id: str
    name: Optional[str]
    quantity: int
    price_each: float
    line_total: float


class CartResponse(BaseModel):
    cart_id: str
    customer_id: Optional[str]
    cart_token: Optional[str]
    items: List[CartItem]
    totals: MoneyBreakdown
    updated_at: datetime
    request: RequestMetadata


class CartDeleteResponse(BaseModel):
    cart_id: str
    deleted: bool
    request: RequestMetadata
