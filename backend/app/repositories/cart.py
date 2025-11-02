"""Data access helpers for cart entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..db.models import Cake, Cart, CartItem


class CartNotFoundError(Exception):
    """Raised when a requested cart could not be located."""


class CartItemCakeNotFoundError(Exception):
    """Raised when an item references a cake that does not exist."""


class CartPriceMismatchError(Exception):
    """Raised when the cart contains items priced differently from the catalog."""

    def __init__(self, mismatches: Sequence[Tuple[str, float, float]]):
        self.mismatches = list(mismatches)
        super().__init__("Cart contains items priced differently from the catalog")


@dataclass(frozen=True)
class PricingRules:
    tax_rate_percent: float = 0.0
    shipping_flat_fee: float = 0.0
    shipping_free_threshold: float = 0.0

    @classmethod
    def from_settings(cls, settings: object) -> "PricingRules":
        return cls(
            tax_rate_percent=getattr(settings, "tax_rate_percent", 0.0),
            shipping_flat_fee=getattr(settings, "shipping_flat_fee", 0.0),
            shipping_free_threshold=getattr(settings, "shipping_free_threshold", 0.0),
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_cart_token(
    existing_token: str | None, requested_token: str | None
) -> str | None:
    if requested_token:
        return requested_token
    return existing_token or str(uuid.uuid4())


def _find_cart_for_update(
    session: Session,
    *,
    customer_id: str | None,
    cart_token: str | None,
) -> Cart | None:
    if customer_id:
        stmt = (
            select(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.cake))
            .where(Cart.customer_id == customer_id)
        )
        cart = session.execute(stmt).unique().scalars().first()
        if cart:
            return cart
    if cart_token:
        stmt = (
            select(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.cake))
            .where(Cart.cart_token == cart_token)
        )
        return session.execute(stmt).unique().scalars().first()
    return None


def _validate_cake_ids(session: Session, items: Iterable[dict[str, object]]) -> None:
    cake_ids = {item["cake_id"] for item in items}
    if not cake_ids:
        return
    stmt = select(func.count()).select_from(Cake).where(Cake.cake_id.in_(cake_ids))
    count = session.scalar(stmt) or 0
    if count != len(cake_ids):
        raise CartItemCakeNotFoundError()


def upsert_cart(
    session: Session,
    *,
    customer_id: str | None,
    cart_token: str | None,
    items: Iterable[dict[str, object]],
) -> Cart:
    _validate_cake_ids(session, items)

    cart = _find_cart_for_update(
        session, customer_id=customer_id, cart_token=cart_token
    )
    if not cart:
        cart = Cart(customer_id=customer_id, cart_token=cart_token)
        session.add(cart)
        session.flush()

    cart.customer_id = customer_id or cart.customer_id
    cart.cart_token = _ensure_cart_token(cart.cart_token, cart_token)

    # Reset items for idempotent upsert
    cart.items.clear()
    for item in items:
        cart.items.append(
            CartItem(
                cake_id=item["cake_id"],
                quantity=item["quantity"],
                price_each=item["price_each"],
            )
        )

    cart.updated_at = _now()
    session.flush()
    session.refresh(cart)
    return cart


def get_cart_by_reference(session: Session, reference: str) -> Cart:
    stmt = (
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.cake))
        .where(Cart.cart_id == reference)
    )
    cart = session.execute(stmt).unique().scalars().first()
    if cart:
        return cart
    stmt = (
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.cake))
        .where(Cart.cart_token == reference)
    )
    cart = session.execute(stmt).unique().scalars().first()
    if not cart:
        raise CartNotFoundError(reference)
    return cart


def delete_cart(session: Session, cart_id: str) -> bool:
    cart = session.get(Cart, cart_id)
    if not cart:
        return False
    session.delete(cart)
    session.flush()
    return True


def _decimal(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_taxes(subtotal: Decimal, pricing: PricingRules) -> Decimal:
    if pricing.tax_rate_percent <= 0:
        return Decimal("0.00")
    rate = Decimal(str(pricing.tax_rate_percent)) / Decimal("100")
    return _quantize(subtotal * rate)


def _compute_shipping(subtotal: Decimal, pricing: PricingRules) -> Decimal:
    if pricing.shipping_flat_fee <= 0:
        return Decimal("0.00")
    threshold = Decimal(str(pricing.shipping_free_threshold))
    if threshold > 0 and subtotal >= threshold:
        return Decimal("0.00")
    return _quantize(Decimal(str(pricing.shipping_flat_fee)))


def validate_cart_prices(
    cart: Cart, *, tolerance: float = 0.0
) -> List[Tuple[str, float, float]]:
    mismatches: List[Tuple[str, float, float]] = []
    tolerance_value = Decimal(str(tolerance)).copy_abs()
    for item in cart.items:
        if not item.cake:
            raise CartItemCakeNotFoundError()
        catalog_price = Decimal(item.cake.price)
        cart_price = Decimal(item.price_each)
        if (catalog_price - cart_price).copy_abs() > tolerance_value:
            mismatches.append(
                (
                    item.cake_id,
                    float(catalog_price.quantize(Decimal("0.01"))),
                    float(cart_price.quantize(Decimal("0.01"))),
                )
            )
    return mismatches


def serialize_cart(
    cart: Cart, pricing: PricingRules | None = None
) -> dict[str, object]:
    pricing = pricing or PricingRules()
    items_payload = []
    subtotal = Decimal("0")
    for item in cart.items:
        line_total = item.price_each * item.quantity
        subtotal += line_total
        items_payload.append(
            {
                "cart_item_id": item.cart_item_id,
                "cake_id": item.cake_id,
                "name": item.cake.name if item.cake else None,
                "quantity": item.quantity,
                "price_each": _decimal(item.price_each),
                "line_total": _decimal(line_total),
            }
        )

    taxes = _compute_taxes(subtotal, pricing)
    shipping = _compute_shipping(subtotal, pricing)
    total = subtotal + taxes + shipping

    return {
        "cart_id": cart.cart_id,
        "customer_id": cart.customer_id,
        "cart_token": cart.cart_token,
        "items": items_payload,
        "totals": {
            "subtotal": _decimal(_quantize(subtotal)),
            "taxes": _decimal(taxes),
            "shipping": _decimal(shipping),
            "total": _decimal(_quantize(total)),
        },
        "updated_at": cart.updated_at,
    }
