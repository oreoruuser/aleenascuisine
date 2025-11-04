"""Helpers for seeding the application catalog with curated cakes."""

from __future__ import annotations

import logging
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.catalog import CURATED_CAKES
from ..db.models import Cake

logger = logging.getLogger("app.seed")


def seed_curated_catalog(session: Session) -> Tuple[int, int]:
    """Ensure the curated cake collection exists in the database.

    Returns a tuple of ``(inserted, updated)`` counts for observability.
    """

    inserted = 0
    updated = 0

    for curated in CURATED_CAKES:
        existing = session.execute(
            select(Cake).where(Cake.slug == curated.slug)
        ).scalar_one_or_none()

        if existing:
            has_changes = False
            if existing.name != curated.name:
                existing.name = curated.name
                has_changes = True
            if existing.description != curated.description:
                existing.description = curated.description
                has_changes = True
            if float(existing.price) != float(curated.price):
                existing.price = curated.price
                has_changes = True
            if existing.currency != curated.currency:
                existing.currency = curated.currency
                has_changes = True
            if existing.category != curated.category:
                existing.category = curated.category
                has_changes = True
            if existing.image_url != curated.image_url:
                existing.image_url = curated.image_url
                has_changes = True
            if existing.is_available is not curated.is_available:
                existing.is_available = curated.is_available
                has_changes = True
            if existing.stock_quantity < curated.stock_quantity:
                existing.stock_quantity = curated.stock_quantity
                has_changes = True

            if has_changes:
                updated += 1
        else:
            session.add(
                Cake(
                    cake_id=curated.cake_id,
                    name=curated.name,
                    slug=curated.slug,
                    description=curated.description,
                    price=curated.price,
                    currency=curated.currency,
                    category=curated.category,
                    image_url=curated.image_url,
                    stock_quantity=curated.stock_quantity,
                    is_available=curated.is_available,
                )
            )
            inserted += 1

    if inserted or updated:
        session.flush()
        logger.info(
            "catalog_seed_completed",
            extra={"inserted": inserted, "updated": updated},
        )

    return inserted, updated
