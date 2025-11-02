"""Schemas for order and payment operations."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .cart import CartItem, MoneyBreakdown
from .common import RequestMetadata


class OrderCreateRequest(BaseModel):
    idempotency_key: str = Field(..., description="Client supplied idempotency token")
    cart_id: Optional[str] = Field(None, description="Existing cart identifier")
    customer_id: Optional[str] = Field(None, description="Associated customer UUID")
    is_test: Optional[bool] = Field(
        None, description="Override Razorpay sandbox flag for the order"
    )


class OrderSummary(BaseModel):
    order_id: str
    status: str
    order_total: float
    currency: str
    created_at: datetime
    payment_status: str
    items: List[CartItem]
    reservation_expires_at: Optional[datetime] = None
    inventory_released: bool = Field(
        False, description="True once reserved stock returns to inventory"
    )


class OrderDetail(OrderSummary):
    customer_id: str
    totals: MoneyBreakdown
    payment_id: Optional[str]
    provider_order_id: Optional[str]
    provider_payment_id: Optional[str]
    idempotency_key: Optional[str]
    updated_at: datetime


class OrderCreateResponse(BaseModel):
    order: OrderDetail
    provider_order_id: str
    request: RequestMetadata


class OrdersListResponse(BaseModel):
    orders: List[OrderSummary]
    request: RequestMetadata


class OrderDetailResponse(BaseModel):
    order: OrderDetail
    request: RequestMetadata


class OrderCancelResponse(BaseModel):
    order: OrderDetail
    request: RequestMetadata


class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = Field(None, ge=0)
    reason: Optional[str]


class RefundResponse(BaseModel):
    payment_id: str
    refund_id: str
    status: str
    request: RequestMetadata


class RazorpayWebhookResponse(BaseModel):
    accepted: bool
    request: RequestMetadata
