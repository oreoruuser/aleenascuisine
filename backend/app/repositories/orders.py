"""Order domain data access helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.sql import Select
from sqlalchemy.orm import Session, joinedload

from ..db.models import Cake, Cart, Order, OrderItem, Payment, RazorpayEvent, Refund
from . import cart as cart_repo


class OrderNotFoundError(Exception):
    """Raised when the requested order is missing."""


class CartMissingError(Exception):
    """Raised when no cart is available for order creation."""


class PaymentNotFoundError(Exception):
    """Raised when a payment cannot be located for refunds."""


class InventoryUnavailableError(Exception):
    """Raised when requested quantities exceed available stock."""


class OrderCancellationNotAllowedError(Exception):
    """Raised when the order cannot be cancelled based on state or time window."""


class OrderStatusUpdateError(Exception):
    """Raised when transitioning an order to the requested status is not permitted."""


class CartEmptyError(Exception):
    """Raised when attempting to create an order from an empty cart."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _decimal(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _base_order_query(where: Select[bool] | None = None) -> Select[tuple[Order]]:
    stmt = select(Order).options(
        joinedload(Order.items).joinedload(OrderItem.cake),
        joinedload(Order.payments),
    )
    if where is not None:
        stmt = stmt.where(where)
    return stmt


def _order_totals_from_cart(cart_payload: Mapping[str, Any]) -> dict[str, float]:
    totals = cart_payload["totals"]  # type: ignore[index]
    return {
        "subtotal": float(totals["subtotal"]),  # type: ignore[index]
        "taxes": float(totals.get("taxes", 0)),  # type: ignore[attr-defined]
        "shipping": float(totals.get("shipping", 0)),  # type: ignore[attr-defined]
        "total": float(totals["total"]),  # type: ignore[index]
    }


def _reserve_inventory(
    session: Session, items: Sequence[OrderItem] | Sequence[Any]
) -> None:
    for item in items:
        cake = (
            item.cake if hasattr(item, "cake") else None
        )  # pragma: no cover - defensive
        cake_id = getattr(item, "cake_id")
        if cake is None:
            cake = session.get(Cake, cake_id)
        if cake is None:
            raise InventoryUnavailableError(cake_id)
        quantity = getattr(item, "quantity")
        if cake.stock_quantity < quantity:
            raise InventoryUnavailableError(cake.cake_id)
        cake.stock_quantity -= quantity
        cake.updated_at = _now()


def _restore_inventory(session: Session, items: Iterable[OrderItem]) -> None:
    for item in items:
        cake = item.cake or session.get(Cake, item.cake_id)
        if not cake:
            continue
        cake.stock_quantity += item.quantity
        cake.updated_at = _now()


def _release_inventory_hold(session: Session, order: Order) -> None:
    if order.inventory_released:
        order.reservation_expires_at = None
        return
    _restore_inventory(session, order.items)
    order.inventory_released = True
    order.reservation_expires_at = None
    order.updated_at = _now()


def _serialize_items(items: Iterable[OrderItem]) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for item in items:
        payload.append(
            {
                "cart_item_id": item.order_item_id,
                "cake_id": item.cake_id,
                "name": item.cake.name if item.cake else None,
                "quantity": item.quantity,
                "price_each": _decimal(item.price_each),
                "line_total": _decimal(item.line_total),
            }
        )
    return payload


_CANCELLATION_WINDOW = timedelta(hours=24)


def expire_stale_reservations(session: Session, now: datetime | None = None) -> int:
    current_time = now or _now()
    stmt = (
        select(Order)
        .options(joinedload(Order.items))
        .where(
            Order.status.in_({"created", "pending"}),
            Order.payment_status == "pending",
            Order.inventory_released.is_(False),
            Order.reservation_expires_at.is_not(None),
            Order.reservation_expires_at < current_time,
        )
    )
    expired_orders = session.execute(stmt).unique().scalars().all()
    for order in expired_orders:
        _release_inventory_hold(session, order)
        order.status = "expired"
        order.payment_status = "cancelled"
        order.updated_at = current_time
    if expired_orders:
        session.flush()
    return len(expired_orders)


def _cancellation_allowed(order: Order) -> bool:
    if order.status not in {"created", "pending", "confirmed"}:
        return False
    created_at = order.created_at or _now()
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age = _now() - created_at
    return age <= _CANCELLATION_WINDOW


def create_order(
    session: Session,
    *,
    idempotency_key: str | None,
    cart: Cart,
    customer_id: str | None,
    is_test: bool,
    pricing: cart_repo.PricingRules | None = None,
    price_match_tolerance: float | None = None,
    reservation_ttl_minutes: int | None = None,
) -> Tuple[Order, bool]:
    if idempotency_key:
        existing = (
            session.execute(_base_order_query(Order.idempotency_key == idempotency_key))
            .unique()
            .scalars()
            .first()
        )
        if existing:
            return existing, False

    if not cart.items:
        raise CartEmptyError(cart.cart_id)

    ttl_minutes = max(reservation_ttl_minutes or 0, 0)
    if ttl_minutes:
        expire_stale_reservations(session)

    pricing = pricing or cart_repo.PricingRules()
    tolerance = price_match_tolerance or 0.0
    mismatches = cart_repo.validate_cart_prices(cart, tolerance=tolerance)
    if mismatches:
        raise cart_repo.CartPriceMismatchError(mismatches)

    cart_payload = cart_repo.serialize_cart(cart, pricing=pricing)
    totals = _order_totals_from_cart(cart_payload)

    _reserve_inventory(session, cart.items)

    expires_at: datetime | None = None
    if ttl_minutes:
        expires_at = _now() + timedelta(minutes=ttl_minutes)

    order = Order(
        cart_id=cart.cart_id,
        customer_id=customer_id or cart.customer_id,
        status="created",
        payment_status="pending",
        currency="INR",
        subtotal=totals["subtotal"],
        taxes=totals["taxes"],
        shipping=totals["shipping"],
        total=totals["total"],
        provider_order_id=None,
        idempotency_key=idempotency_key,
        is_test=is_test,
        reservation_expires_at=expires_at,
        inventory_released=False,
    )
    session.add(order)
    session.flush()

    order.items.clear()
    for item in cart.items:
        line_total = item.price_each * item.quantity
        order.items.append(
            OrderItem(
                cake_id=item.cake_id,
                quantity=item.quantity,
                price_each=item.price_each,
                line_total=line_total,
            )
        )

    payment = Payment(
        order_id=order.order_id,
        amount=order.total,
        currency=order.currency,
        status="pending",
        provider_payment_id=None,
    )
    session.add(payment)

    order.updated_at = _now()
    session.flush()
    session.refresh(order)
    return order, True


def get_order(session: Session, order_id: str) -> Order:
    stmt = _base_order_query(Order.order_id == order_id)
    order = session.execute(stmt).unique().scalars().first()
    if not order:
        raise OrderNotFoundError(order_id)
    return order


def list_orders(session: Session, customer_id: str) -> list[Order]:
    stmt = _base_order_query(Order.customer_id == customer_id).order_by(
        Order.created_at.desc()
    )
    return session.execute(stmt).unique().scalars().all()


def cancel_order(session: Session, order_id: str) -> Order:
    order = get_order(session, order_id)
    if not _cancellation_allowed(order):
        raise OrderCancellationNotAllowedError(order_id)

    _release_inventory_hold(session, order)

    order.status = "cancelled"
    order.payment_status = "cancelled"
    order.updated_at = _now()
    for payment in order.payments:
        if payment.status not in {"refunded", "refund_requested"}:
            payment.status = "cancelled"
    session.flush()
    session.refresh(order)
    return order


def set_provider_order_reference(
    session: Session, order: Order, provider_order_id: str
) -> Order:
    order.provider_order_id = provider_order_id
    order.updated_at = _now()
    session.flush()
    session.refresh(order)
    return order


def apply_payment_event(
    session: Session, payload: Mapping[str, Any]
) -> tuple[Order | None, Payment | None]:
    event_type = payload.get("event")
    payment_payload = (
        payload.get("payload", {})  # type: ignore[call-arg]
        .get("payment", {})  # type: ignore[call-arg]
        .get("entity", {})
    )
    order_payload = (
        payload.get("payload", {})  # type: ignore[call-arg]
        .get("order", {})  # type: ignore[call-arg]
        .get("entity", {})
    )

    provider_payment_id = payment_payload.get("id")
    provider_order_id = payment_payload.get("order_id") or order_payload.get("id")

    payment: Payment | None = None
    if provider_payment_id:
        stmt = select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        payment = session.execute(stmt).scalar_one_or_none()

    if payment is None and provider_order_id:
        stmt = (
            select(Payment)
            .join(Order, Payment.order_id == Order.order_id)
            .where(Order.provider_order_id == provider_order_id)
        )
        payment = session.execute(stmt).scalars().first()
        if (
            payment
            and provider_payment_id
            and payment.provider_payment_id != provider_payment_id
        ):
            payment.provider_payment_id = provider_payment_id

    if payment is None:
        return None, None

    if provider_payment_id and payment.provider_payment_id != provider_payment_id:
        payment.provider_payment_id = provider_payment_id

    order = payment.order
    if event_type and event_type.startswith("refund"):
        payment.status = "refunded"
        order.payment_status = "refunded"
        order.status = "refunded"
        _release_inventory_hold(session, order)
    else:
        status = payment_payload.get("status") or event_type
        if status:
            payment.status = status
            if order.status not in {"cancelled", "refunded"}:
                if status in {"authorized", "captured"}:
                    order.payment_status = (
                        "paid" if status == "captured" else "authorized"
                    )
                    if order.status in {"created", "pending"}:
                        order.status = "confirmed"
                    order.reservation_expires_at = None
                    order.inventory_released = False
                elif status in {"failed", "declined"}:
                    order.payment_status = "failed"
                    order.status = "payment_failed"
                    _release_inventory_hold(session, order)

    order.updated_at = _now()
    session.flush()
    session.refresh(order)
    return order, payment


_ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "created": {"pending", "confirmed", "cancelled", "expired"},
    "pending": {"confirmed", "cancelled", "expired"},
    "confirmed": {"processing", "shipped", "cancelled"},
    "processing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
    "refunded": set(),
    "payment_failed": set(),
    "expired": set(),
}


def update_order_status(session: Session, order_id: str, status: str) -> Order:
    order = get_order(session, order_id)
    current = order.status
    if status == current:
        return order
    allowed = _ALLOWED_STATUS_TRANSITIONS.get(current, set())
    if status not in allowed:
        raise OrderStatusUpdateError(f"Cannot transition from {current} to {status}")

    if status == "cancelled" and current != "cancelled":
        _release_inventory_hold(session, order)

    order.status = status
    if status == "delivered":
        order.payment_status = order.payment_status or "paid"
    if status == "cancelled":
        order.payment_status = "cancelled"
        for payment in order.payments:
            if payment.status not in {"refunded", "refund_requested"}:
                payment.status = "cancelled"
    if status == "expired":
        order.payment_status = "cancelled"
        _release_inventory_hold(session, order)
    order.updated_at = _now()
    session.flush()
    session.refresh(order)
    return order


def serialize_order_summary(order: Order) -> dict[str, object]:
    return {
        "order_id": order.order_id,
        "status": order.status,
        "order_total": _decimal(order.total),
        "currency": order.currency,
        "created_at": order.created_at,
        "payment_status": order.payment_status,
        "items": _serialize_items(order.items),
        "reservation_expires_at": order.reservation_expires_at,
        "inventory_released": order.inventory_released,
    }


def serialize_order_detail(order: Order) -> dict[str, object]:
    items_payload = _serialize_items(order.items)

    totals = {
        "subtotal": _decimal(order.subtotal),
        "taxes": _decimal(order.taxes),
        "shipping": _decimal(order.shipping),
        "total": _decimal(order.total),
    }

    payment_id = order.payments[0].payment_id if order.payments else None

    return {
        "order_id": order.order_id,
        "order_total": _decimal(order.total),
        "currency": order.currency,
        "customer_id": order.customer_id,
        "items": items_payload,
        "totals": totals,
        "payment_id": payment_id,
        "payment_status": order.payment_status,
        "provider_order_id": order.provider_order_id,
        "provider_payment_id": order.payments[0].provider_payment_id
        if order.payments
        else None,
        "idempotency_key": order.idempotency_key,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "reservation_expires_at": order.reservation_expires_at,
        "inventory_released": order.inventory_released,
    }


def record_webhook(
    session: Session,
    *,
    headers: dict[str, str],
    payload: dict[str, object],
    signature: str,
) -> RazorpayEvent:
    event = RazorpayEvent(
        headers_json=json.dumps(headers, default=str),
        payload_json=json.dumps(payload, default=str),
        signature=signature,
    )
    session.add(event)
    session.flush()
    return event


def get_payment(session: Session, payment_id: str) -> Payment:
    payment = session.get(Payment, payment_id)
    if not payment:
        raise PaymentNotFoundError(payment_id)
    return payment


def request_refund(
    session: Session,
    *,
    payment: Payment,
    amount: float | None,
    reason: str | None,
) -> Refund:
    refund_amount = amount or _decimal(payment.amount)
    refund = Refund(
        payment_id=payment.payment_id,
        amount=refund_amount,
        status="requested",
        reason=reason,
    )
    payment.status = "refund_requested"
    payment.order.payment_status = "refund_requested"
    if payment.order.status not in {"refunded", "cancelled"}:
        payment.order.status = "refund_initiated"
    payment.order.updated_at = _now()
    session.add(refund)
    session.flush()
    session.refresh(refund)
    return refund
