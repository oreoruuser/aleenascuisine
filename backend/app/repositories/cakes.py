"""Data access helpers for cake catalog entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db.models import Cake


class CakeNotFoundError(Exception):
    """Raised when a cake record cannot be located."""


class DuplicateCakeSlugError(Exception):
    """Raised when attempting to create a cake with an existing slug."""


class InvalidInventoryAdjustmentError(Exception):
    """Raised when an inventory adjustment would result in a negative quantity."""


def _current_time() -> datetime:
    return datetime.now(timezone.utc)


def _get_by_slug(session: Session, slug: str) -> Cake | None:
    stmt = select(Cake).where(Cake.slug == slug)
    return session.execute(stmt).scalar_one_or_none()


def list_cakes(
    session: Session,
    *,
    search: str | None,
    category: str | None,
    min_price: float | None,
    max_price: float | None,
    page: int,
    page_size: int,
) -> Tuple[list[Cake], int]:
    base_query = select(Cake)

    if search:
        pattern = f"%{search.lower()}%"
        base_query = base_query.where(
            or_(
                func.lower(Cake.name).like(pattern),
                func.lower(Cake.slug).like(pattern),
                func.lower(Cake.description).like(pattern),
            )
        )
    if category:
        base_query = base_query.where(func.lower(Cake.category) == category.lower())
    if min_price is not None:
        base_query = base_query.where(Cake.price >= min_price)
    if max_price is not None:
        base_query = base_query.where(Cake.price <= max_price)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = session.scalar(count_query) or 0

    stmt = (
        base_query.order_by(Cake.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    cakes = session.execute(stmt).scalars().all()
    return cakes, int(total)


def get_cake(session: Session, cake_id: str) -> Cake:
    cake = session.get(Cake, cake_id)
    if not cake:
        raise CakeNotFoundError(cake_id)
    return cake


def create_cake(
    session: Session,
    *,
    name: str,
    slug: str,
    description: str | None,
    price: float,
    currency: str,
    category: str | None,
    is_available: bool,
    stock_quantity: int,
    image_url: str | None,
) -> Cake:
    if _get_by_slug(session, slug):
        raise DuplicateCakeSlugError(slug)

    cake = Cake(
        name=name,
        slug=slug,
        description=description,
        price=price,
        currency=currency,
        category=category,
        is_available=is_available,
        stock_quantity=stock_quantity,
        image_url=image_url,
    )
    session.add(cake)
    session.flush()
    session.refresh(cake)
    return cake


def update_cake(
    session: Session,
    cake_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    price: float | None = None,
    currency: str | None = None,
    category: str | None = None,
    is_available: bool | None = None,
    stock_quantity: int | None = None,
    image_url: str | None = None,
) -> Cake:
    cake = get_cake(session, cake_id)

    if name is not None:
        cake.name = name
    if description is not None:
        cake.description = description
    if price is not None:
        cake.price = price
    if currency is not None:
        cake.currency = currency
    if category is not None:
        cake.category = category
    if is_available is not None:
        cake.is_available = is_available
    if stock_quantity is not None:
        if stock_quantity < 0:
            raise InvalidInventoryAdjustmentError(cake_id)
        cake.stock_quantity = stock_quantity
    if image_url is not None:
        cake.image_url = image_url

    cake.updated_at = _current_time()
    session.flush()
    session.refresh(cake)
    return cake


def set_availability(session: Session, cake_id: str, is_available: bool) -> Cake:
    cake = get_cake(session, cake_id)
    cake.is_available = is_available
    cake.updated_at = _current_time()
    session.flush()
    session.refresh(cake)
    return cake


def adjust_inventory(session: Session, cake_id: str, delta: int) -> Cake:
    cake = get_cake(session, cake_id)
    new_quantity = cake.stock_quantity + delta
    if new_quantity < 0:
        raise InvalidInventoryAdjustmentError(cake_id)
    cake.stock_quantity = new_quantity
    cake.updated_at = _current_time()
    session.flush()
    session.refresh(cake)
    return cake


def to_summary_dict(cake: Cake) -> dict[str, object]:
    return {
        "cake_id": cake.cake_id,
        "name": cake.name,
        "slug": cake.slug,
        "price": float(cake.price),
        "currency": cake.currency,
        "category": cake.category,
        "is_available": cake.is_available,
    }


def to_detail_dict(cake: Cake) -> dict[str, object]:
    data = cake.to_dict()
    return data
