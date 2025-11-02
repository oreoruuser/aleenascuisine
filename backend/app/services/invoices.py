"""Invoice generation helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Any, Mapping

from sqlalchemy.orm import Session

try:  # pragma: no cover - optional dependency for production path
    import boto3  # type: ignore
except ImportError:  # pragma: no cover - degrade gracefully
    boto3 = None  # type: ignore

from ..core.config import Settings
from ..db.models import Order
from ..repositories import invoices as invoice_repo

logger = logging.getLogger(__name__)


class InvoiceGenerationError(RuntimeError):
    """Raised when an invoice could not be generated."""


class InvoiceService:
    """Render invoice payloads and persist them to S3/invoices table."""

    def __init__(self, settings: Settings, *, s3_client: Any | None = None) -> None:
        bucket = settings.s3_bucket_invoices
        if not bucket:
            raise InvoiceGenerationError("S3_BUCKET_INVOICES is not configured")
        if boto3 is None and s3_client is None:
            raise InvoiceGenerationError("boto3 is required for invoice uploads")
        self._bucket = bucket
        self._settings = settings
        self._s3 = s3_client or boto3.client("s3")  # type: ignore[call-arg]

    def _render_invoice_payload(self, order: Order) -> Mapping[str, Any]:
        lines = []
        subtotal = Decimal("0")
        for item in order.items:
            line_total = Decimal(item.line_total)
            subtotal += line_total
            lines.append(
                {
                    "cake_id": item.cake_id,
                    "name": item.cake.name if item.cake else None,
                    "quantity": item.quantity,
                    "price_each": float(item.price_each),
                    "line_total": float(line_total),
                }
            )
        payload = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "created_at": (order.created_at or datetime.now(timezone.utc)).isoformat(),
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "currency": order.currency,
            "subtotal": float(subtotal),
            "taxes": float(order.taxes or 0),
            "shipping": float(order.shipping or 0),
            "total": float(order.total or 0),
            "items": lines,
        }
        return payload

    def _build_key(self, order: Order) -> str:
        now = datetime.now(timezone.utc)
        path = PurePosixPath(
            "invoices",
            order.order_id,
            f"invoice_{now.strftime('%Y%m%dT%H%M%SZ')}" + ".json",
        )
        return str(path)

    def generate_and_store(self, session: Session, order: Order):
        payload = self._render_invoice_payload(order)
        key = self._build_key(order)
        logger.info(
            "Uploading invoice to S3",
            extra={"bucket": self._bucket, "key": key, "order_id": order.order_id},
        )
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._s3.put_object(
            Bucket=self._bucket, Key=key, Body=body, ContentType="application/json"
        )
        invoice = invoice_repo.create_invoice(
            session,
            order_id=order.order_id,
            bucket=self._bucket,
            key=key,
            total=Decimal(str(order.total or 0)),
            taxes=Decimal(str(order.taxes or 0)),
        )
        return invoice
