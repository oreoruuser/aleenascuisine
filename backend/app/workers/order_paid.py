"""SQS worker to process order.paid events."""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterable

from ..core.config import get_settings
from ..core.tracing import add_tracing_metadata, init_tracing, xray_subsegment
from ..db.session import get_db_session
from ..repositories import orders as order_repo
from ..repositories import invoices as invoice_repo
from ..services.invoices import InvoiceGenerationError, InvoiceService
from ..services.notifications import NotificationService, create_notification_service

logger = logging.getLogger(__name__)


def _init_tracing(settings) -> None:
    init_tracing(f"aleenascuisine-{settings.aleena_env}-worker")


def _parse_message(body: str) -> Dict[str, Any]:
    message = json.loads(body)
    if "Message" in message and isinstance(message["Message"], str):
        return json.loads(message["Message"])
    return message


@contextmanager
def _session_scope(database_url: str):
    iterator = get_db_session(database_url)
    session = next(iterator)
    try:
        yield session
    finally:
        try:
            next(iterator)
        except StopIteration:
            pass


def _process_order_paid(
    message: Dict[str, Any],
    invoice_service: InvoiceService,
    database_url: str,
    notification_service: NotificationService | None,
) -> None:
    payload = message.get("payload", {})
    order_id = payload.get("order_id")
    if not order_id:
        logger.warning(
            "order.paid message missing order_id", extra={"message": message}
        )
        return
    add_tracing_metadata(order_id=order_id)
    with _session_scope(database_url) as session:
        with xray_subsegment("db.get_order", order_id=order_id):
            order = order_repo.get_order(session, order_id)
        try:
            with xray_subsegment("db.get_invoice", order_id=order_id):
                invoice_repo.get_latest_invoice_for_order(session, order_id)
            logger.info(
                "Invoice already exists for order; skipping generation",
                extra={"order_id": order_id},
            )
            return
        except invoice_repo.InvoiceNotFoundError:
            pass
        try:
            with xray_subsegment("service.generate_invoice", order_id=order_id):
                invoice = invoice_service.generate_and_store(session, order)
        except InvoiceGenerationError as exc:
            logger.error(
                "Invoice generation failed",
                extra={"order_id": order_id, "reason": str(exc)},
            )
            raise
        if notification_service:
            notification_service.notify_order_paid(order, invoice)
        logger.info(
            "Invoice generated",
            extra={"order_id": order_id, "invoice_id": invoice.invoice_id},
        )


def _process_status_update(
    message: Dict[str, Any],
    database_url: str,
    notification_service: NotificationService | None,
    event_type: str,
) -> None:
    payload = message.get("payload", {})
    order_id = payload.get("order_id")
    if not order_id:
        logger.warning(
            "order status message missing order_id",
            extra={"message": message},
        )
        return
    if notification_service is None:
        logger.info(
            "Notification service unavailable; skipping status update",
            extra={"order_id": order_id, "event_type": event_type},
        )
        return
    add_tracing_metadata(order_id=order_id, event_type=event_type)
    with _session_scope(database_url) as session:
        with xray_subsegment("db.get_order", order_id=order_id):
            order = order_repo.get_order(session, order_id)
        if event_type == "order.refunded":
            notification_service.notify_order_refunded(order)
        elif event_type == "order.payment_failed":
            notification_service.notify_payment_failed(order)
        else:
            logger.info(
                "Unhandled status update event",
                extra={"order_id": order_id, "event_type": event_type},
            )


def handle(event: Dict[str, Any], _context: Any | None = None) -> Dict[str, Any]:
    settings = get_settings()
    _init_tracing(settings)
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for worker execution")
    invoice_service = InvoiceService(settings)
    notification_service = create_notification_service(settings)
    processed = 0
    errors: list[Dict[str, Any]] = []
    records: Iterable[Dict[str, Any]] = event.get("Records", [])
    for record in records:
        body = record.get("body")
        if not body:
            continue
        try:
            message = _parse_message(body)
            message_type = message.get("type")
            if message_type == "order.paid":
                _process_order_paid(
                    message,
                    invoice_service,
                    settings.database_url,
                    notification_service,
                )
                processed += 1
            elif message_type in {"order.refunded", "order.payment_failed"}:
                _process_status_update(
                    message,
                    settings.database_url,
                    notification_service,
                    message_type,
                )
                processed += 1
            else:
                logger.info("Skipping message", extra={"type": message_type})
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to process order.paid message", exc_info=exc)
            errors.append({"error": str(exc), "record": record})
    return {"processed": processed, "errors": errors}
