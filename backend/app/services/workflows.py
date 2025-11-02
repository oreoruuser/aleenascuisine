"""Domain workflows that decouple side effects such as notifications."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Protocol

from ..db.models import Order

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import boto3  # type: ignore
except ImportError:  # pragma: no cover - degrade when boto3 unavailable
    boto3 = None  # type: ignore


class NotificationDispatcher(Protocol):
    """Protocol describing notification dispatchers."""

    def send_order_confirmation(
        self, order: Order
    ) -> None:  # pragma: no cover - protocol
        ...

    def enqueue_post_payment_jobs(
        self, order: Order
    ) -> None:  # pragma: no cover - protocol
        ...


class LoggingNotificationDispatcher:
    """Default dispatcher that simply logs operations."""

    def send_order_confirmation(self, order: Order) -> None:
        logger.info(
            "Order confirmation notification queued", extra={"order_id": order.order_id}
        )

    def enqueue_post_payment_jobs(self, order: Order) -> None:
        logger.info(
            "Post-payment jobs enqueued",
            extra={"order_id": order.order_id, "status": order.status},
        )


class SQSNotificationDispatcher:
    """Publish order events to Amazon SQS for asynchronous processing."""

    def __init__(self, queue_url: str, *, client: Any | None = None) -> None:
        if boto3 is None and client is None:
            raise RuntimeError("boto3 is required for SQS notifications")
        self._queue_url = queue_url
        self._client = client or boto3.client("sqs")  # type: ignore[call-arg]

    def _send(self, message_type: str, payload: Mapping[str, Any]) -> None:
        body = json.dumps({"type": message_type, "payload": payload})
        logger.info(
            "Publishing notification",
            extra={
                "queue_url": self._queue_url,
                "type": message_type,
                "order_id": payload.get("order_id"),
            },
        )
        self._client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=body,
            MessageAttributes={
                "type": {
                    "StringValue": message_type,
                    "DataType": "String",
                }
            },
        )

    def send_order_confirmation(self, order: Order) -> None:
        self._send(
            "order.notification",
            {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "status": order.status,
                "total": float(order.total),
            },
        )

    def enqueue_post_payment_jobs(self, order: Order) -> None:
        self._send(
            "order.paid",
            {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "amount": float(order.total),
                "currency": order.currency,
            },
        )
