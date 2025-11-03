"""Declarative SQLAlchemy models for the Aleena's Cuisine API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


def _default_uuid() -> str:
    return str(uuid.uuid4())


def _coerce_decimal(value: Decimal | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return value


class Cake(Base):
    __tablename__ = "cakes"

    cake_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    cart_items = relationship("CartItem", back_populates="cake")
    order_items = relationship("OrderItem", back_populates="cake")

    def to_dict(self) -> dict[str, object]:
        """Serialize a cake instance for schema conversion."""

        return {
            "cake_id": self.cake_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price": _coerce_decimal(self.price),
            "currency": self.currency,
            "image_url": self.image_url,
            "category": self.category,
            "stock_quantity": self.stock_quantity,
            "is_available": self.is_available,
            "created_at": self.created_at or datetime.now(timezone.utc),
            "updated_at": self.updated_at or datetime.now(timezone.utc),
        }


class Cart(Base):
    __tablename__ = "carts"

    cart_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    cart_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_item_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    cart_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("carts.cart_id", ondelete="CASCADE"), nullable=False
    )
    cake_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cakes.cake_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_each: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    cart = relationship("Cart", back_populates="items")
    cake = relationship("Cake", back_populates="cart_items")

    def line_total(self) -> float:
        return _coerce_decimal(self.price_each) * self.quantity


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    cart_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    payment_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    taxes: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    shipping: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    provider_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    reservation_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    inventory_released: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False
    )
    cake_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cakes.cake_id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_each: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    cake = relationship("Cake", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="initiated")
    provider_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    order = relationship("Order", back_populates="payments")
    refunds: Mapped[list["Refund"]] = relationship(
        "Refund",
        back_populates="payment",
        cascade="all, delete-orphan",
    )


class Refund(Base):
    __tablename__ = "refunds"

    refund_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    payment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payments.payment_id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payment = relationship("Payment", back_populates="refunds")


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False
    )
    s3_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(256), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    taxes: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    order = relationship("Order", back_populates="invoices")


class RazorpayEvent(Base):
    __tablename__ = "razorpay_events"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_default_uuid
    )
    signature: Mapped[str | None] = mapped_column(String(256), nullable=True)
    headers_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
