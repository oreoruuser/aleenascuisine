"""SQS worker to process order.paid events."""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterable

from ..core.config import get_settings
from ..db.session import get_db_session
from ..repositories import orders as order_repo
from ..services.invoices import InvoiceGenerationError, InvoiceService
from ..services.workflows import LoggingNotificationDispatcher

logger = logging.getLogger(__name__)


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
    message: Dict[str, Any], invoice_service: InvoiceService, database_url: str
) -> None:
    payload = message.get("payload", {})
    order_id = payload.get("order_id")
    if not order_id:
        logger.warning(
            "order.paid message missing order_id", extra={"message": message}
        )
        return
    with _session_scope(database_url) as session:
        order = order_repo.get_order(session, order_id)
        try:
            invoice = invoice_service.generate_and_store(session, order)
        except InvoiceGenerationError as exc:
            logger.error(
                "Invoice generation failed",
                extra={"order_id": order_id, "reason": str(exc)},
            )
            raise
        dispatcher = LoggingNotificationDispatcher()
        dispatcher.send_order_confirmation(order)
        logger.info(
            "Invoice generated",
            extra={"order_id": order_id, "invoice_id": invoice.invoice_id},
        )


def handle(event: Dict[str, Any], _context: Any | None = None) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for worker execution")
    invoice_service = InvoiceService(settings)
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
                _process_order_paid(message, invoice_service, settings.database_url)
                processed += 1
            else:
                logger.info("Skipping message", extra={"type": message_type})
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to process order.paid message", exc_info=exc)
            errors.append({"error": str(exc), "record": record})
    return {"processed": processed, "errors": errors}
