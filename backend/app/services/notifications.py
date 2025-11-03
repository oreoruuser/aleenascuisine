"""Notification helpers for customer and admin alerts."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Optional

try:  # pragma: no cover - optional dependency
    import boto3  # type: ignore
except ImportError:  # pragma: no cover - degrade when boto3 unavailable
    boto3 = None  # type: ignore

from ..core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _WhatsAppClient:
    access_token: str
    phone_number_id: str
    api_version: str
    default_recipient: str

    def send_text(self, message: str, *, recipient: Optional[str] = None) -> None:
        url = (
            f"https://graph.facebook.com/{self.api_version}/"
            f"{self.phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient or self.default_recipient,
            "type": "text",
            "text": {"body": message},
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10):  # pragma: no cover - I/O
                logger.info(
                    "WhatsApp notification queued",
                    extra={"recipient": recipient or self.default_recipient},
                )
        except urllib.error.URLError as exc:  # pragma: no cover - network failure
            logger.warning(
                "WhatsApp notification failed",
                extra={"error": str(exc)},
            )


class NotificationService:
    """Dispatch order notifications to configured channels."""

    def __init__(
        self,
        settings: Settings,
        *,
        sns_client: Any | None = None,
        secrets_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._sns_topic_arn = settings.admin_notifications_topic_arn
        self._sns = None
        if self._sns_topic_arn:
            if sns_client is not None:
                self._sns = sns_client
            elif boto3 is not None:
                self._sns = boto3.client("sns")  # type: ignore[assignment]
            else:  # pragma: no cover - boto3 missing locally
                logger.warning(
                    "SNS client unavailable; admin notifications disabled",
                )
        self._whatsapp: _WhatsAppClient | None = None
        if (
            settings.whatsapp_secret_arn
            and settings.whatsapp_phone_number_id
            and settings.whatsapp_default_recipient
        ):
            token = self._load_whatsapp_token(secrets_client)
            if token:
                self._whatsapp = _WhatsAppClient(
                    access_token=token,
                    phone_number_id=settings.whatsapp_phone_number_id,
                    api_version=settings.whatsapp_api_version,
                    default_recipient=settings.whatsapp_default_recipient,
                )

    def _load_whatsapp_token(self, secrets_client: Any | None) -> Optional[str]:
        client = secrets_client
        if client is None and boto3 is not None:
            client = boto3.client("secretsmanager")  # type: ignore[assignment]
        if client is None:  # pragma: no cover - boto3 not installed
            logger.warning(
                "Secrets Manager client unavailable; WhatsApp notifications disabled",
            )
            return None
        try:
            secret = client.get_secret_value(
                SecretId=self._settings.whatsapp_secret_arn
            )
        except Exception as exc:  # pragma: no cover - AWS error surface
            logger.warning(
                "Unable to load WhatsApp secret",
                extra={"error": str(exc)},
            )
            return None
        secret_string = secret.get("SecretString") or ""
        token = secret_string
        try:
            parsed = json.loads(secret_string)
            token = (
                parsed.get("access_token")
                or parsed.get("token")
                or parsed.get("whatsapp_token")
            )
        except json.JSONDecodeError:
            token = secret_string
        if not token:
            logger.warning("WhatsApp secret did not contain an access token")
            return None
        return token

    def notify_order_paid(self, order, invoice=None) -> None:
        """Notify channels that an order payment succeeded."""

        summary = self._build_summary(order, invoice)
        self._publish_admin_update(
            summary,
            event="order.paid",
            subject=f"Order {summary.get('order_id')} paid",
        )
        self._send_whatsapp(summary)

    def notify_order_refunded(self, order) -> None:
        summary = self._build_summary(order, None)
        self._publish_admin_update(
            summary,
            event="order.refunded",
            subject=f"Order {summary.get('order_id')} refunded",
        )

    def notify_payment_failed(self, order) -> None:
        summary = self._build_summary(order, None)
        self._publish_admin_update(
            summary,
            event="order.payment_failed",
            subject=f"Order {summary.get('order_id')} payment failed",
        )

    def _build_summary(self, order, invoice) -> Mapping[str, Any]:
        invoice_location: Optional[str] = None
        if invoice is not None:
            invoice_location = f"s3://{invoice.s3_bucket}/{invoice.s3_key}"
        payload = {
            "order_id": getattr(order, "order_id", None),
            "customer_id": getattr(order, "customer_id", None),
            "total": float(getattr(order, "total", 0) or 0),
            "currency": getattr(order, "currency", "INR"),
            "status": getattr(order, "status", None),
            "payment_status": getattr(order, "payment_status", None),
            "is_test": getattr(order, "is_test", False),
            "invoice_location": invoice_location,
        }
        return payload

    def _publish_admin_update(
        self, payload: Mapping[str, Any], *, event: str, subject: str
    ) -> None:
        if not self._sns or not self._sns_topic_arn:
            return
        message = json.dumps(payload, separators=(",", ":"))
        try:
            self._sns.publish(
                TopicArn=self._sns_topic_arn,
                Subject=subject,
                Message=message,
                MessageAttributes={
                    "event": {"DataType": "String", "StringValue": event}
                },
            )
        except Exception as exc:  # pragma: no cover - AWS error surface
            logger.warning(
                "Failed to publish admin notification",
                extra={"error": str(exc)},
            )

    def _send_whatsapp(self, payload: Mapping[str, Any]) -> None:
        if not self._whatsapp:
            return
        message = "Order {order_id} is paid. Total: {total} {currency}.".format(
            order_id=payload.get("order_id"),
            total=payload.get("total"),
            currency=payload.get("currency"),
        )
        if payload.get("invoice_location"):
            message += f" Invoice: {payload['invoice_location']}"
        self._whatsapp.send_text(message)


def create_notification_service(settings: Settings) -> NotificationService | None:
    """Attempt to create a notification service from runtime settings."""

    if not (
        settings.admin_notifications_topic_arn
        or (
            settings.whatsapp_secret_arn
            and settings.whatsapp_phone_number_id
            and settings.whatsapp_default_recipient
        )
    ):
        return None
    try:
        return NotificationService(settings)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "Notification service initialization failed",
            extra={"error": str(exc)},
        )
        return None
