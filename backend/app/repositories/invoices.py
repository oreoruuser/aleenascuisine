"""Invoice persistence helpers."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Invoice


class InvoiceNotFoundError(Exception):
    """Raised when an invoice record is missing."""


def create_invoice(
    session: Session,
    *,
    order_id: str,
    bucket: str,
    key: str,
    total: Decimal | float,
    taxes: Decimal | float,
) -> Invoice:
    invoice = Invoice(
        order_id=order_id,
        s3_bucket=bucket,
        s3_key=key,
        total=Decimal(str(total)),
        taxes=Decimal(str(taxes)),
    )
    session.add(invoice)
    session.flush()
    session.refresh(invoice)
    return invoice


def get_latest_invoice_for_order(session: Session, order_id: str) -> Invoice:
    stmt = (
        select(Invoice)
        .where(Invoice.order_id == order_id)
        .order_by(Invoice.created_at.desc())
    )
    invoice = session.execute(stmt).scalars().first()
    if not invoice:
        raise InvoiceNotFoundError(order_id)
    return invoice
