"""Razorpay API integration helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

try:  # pragma: no cover - import guarded for optional dependency
    import razorpay  # type: ignore
except ImportError:  # pragma: no cover - library optional in some environments
    razorpay = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from razorpay import Client as RazorpayClient  # type: ignore
    from razorpay.errors import SignatureVerificationError  # type: ignore
else:
    RazorpayClient = Any  # type: ignore
    if razorpay is not None:  # pragma: no cover - exercised in production runtime
        try:
            from razorpay.errors import SignatureVerificationError  # type: ignore
        except Exception:  # pragma: no cover - defensive fallback

            class SignatureVerificationError(Exception):
                """Fallback signature verification error when Razorpay SDK is partially available."""

    else:

        class SignatureVerificationError(Exception):
            """Fallback signature verification error when Razorpay SDK is absent."""


logger = logging.getLogger(__name__)


class RazorpayConfigurationError(RuntimeError):
    """Raised when Razorpay credentials are missing."""


class RazorpayWebhookVerificationError(RuntimeError):
    """Raised when webhook signature verification fails."""


@dataclass
class RazorpayOrderResult:
    """Normalized result after creating an order with Razorpay."""

    id: str
    status: str
    amount: int
    currency: str
    raw: Dict[str, Any]


@dataclass
class RazorpayRefundResult:
    """Normalized result after initiating a refund."""

    id: Optional[str]
    status: Optional[str]
    amount: Optional[int]
    raw: Dict[str, Any]


class RazorpayService:
    """Thin wrapper around the official Razorpay Python SDK."""

    def __init__(
        self,
        *,
        key_id: str | None,
        key_secret: str | None,
        webhook_secret: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not key_id or not key_secret:
            raise RazorpayConfigurationError(
                "Razorpay credentials are required. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."
            )
        if razorpay is None:
            raise RazorpayConfigurationError(
                "The razorpay package is not installed. Add razorpay to requirements."
            )
        client_factory = getattr(razorpay, "Client", None)
        if client_factory is None:
            raise RazorpayConfigurationError(
                "The razorpay package is available but Client factory is missing."
            )
        self._client = client or client_factory(auth=(key_id, key_secret))  # type: ignore[call-arg]
        self._webhook_secret = webhook_secret

    def create_order(
        self,
        *,
        amount_paise: int,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
        test_mode: bool = False,
    ) -> RazorpayOrderResult:
        payload: Dict[str, Any] = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
            "payment_capture": 1,
        }
        if test_mode:
            payload["notes"]["test_mode"] = True
        logger.debug("Creating Razorpay order", extra={"payload": payload})
        raw = self._client.order.create(payload)
        return RazorpayOrderResult(
            id=raw.get("id"),
            status=raw.get("status"),
            amount=raw.get("amount"),
            currency=raw.get("currency"),
            raw=raw,
        )

    def request_refund(
        self,
        *,
        payment_id: str,
        amount_paise: Optional[int] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> RazorpayRefundResult:
        payload: Dict[str, Any] = {}
        if amount_paise is not None:
            payload["amount"] = amount_paise
        if notes:
            payload["notes"] = notes
        logger.debug(
            "Initiating Razorpay refund",
            extra={"payment_id": payment_id, "payload": payload},
        )
        raw = self._client.payment.refund(payment_id, payload)  # type: ignore[no-any-return]
        return RazorpayRefundResult(
            id=raw.get("id"),
            status=raw.get("status"),
            amount=raw.get("amount"),
            raw=raw,
        )

    def verify_webhook_signature(self, body: bytes, signature: str | None) -> None:
        if not self._webhook_secret:
            raise RazorpayWebhookVerificationError(
                "Webhook secret is not configured. Set RAZORPAY_WEBHOOK_SECRET."
            )
        if not signature:
            raise RazorpayWebhookVerificationError("Webhook signature header missing.")
        try:
            utility = getattr(razorpay, "utility", None)
            if utility is None:
                raise RazorpayWebhookVerificationError(
                    "Razorpay utility module is unavailable for signature verification."
                )
            utility.verify_webhook_signature(  # type: ignore[attr-defined]
                body.decode("utf-8"), signature, self._webhook_secret
            )
        except SignatureVerificationError as exc:  # pragma: no cover - SDK surface
            raise RazorpayWebhookVerificationError("Invalid webhook signature") from exc


class StubRazorpayService(RazorpayService):
    """In-memory Razorpay implementation for testing."""

    def __init__(self) -> None:  # pragma: no cover - trivial
        self._orders: Dict[str, RazorpayOrderResult] = {}
        self._refunds: list[RazorpayRefundResult] = []
        self._counter = 0

    def create_order(
        self,
        *,
        amount_paise: int,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
        test_mode: bool = False,
    ) -> RazorpayOrderResult:
        self._counter += 1
        order_id = f"order_stub_{self._counter:05d}"
        result = RazorpayOrderResult(
            id=order_id,
            status="created",
            amount=amount_paise,
            currency=currency,
            raw={
                "id": order_id,
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
                "status": "created",
                "test_mode": test_mode,
            },
        )
        self._orders[order_id] = result
        return result

    def request_refund(
        self,
        *,
        payment_id: str,
        amount_paise: Optional[int] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> RazorpayRefundResult:
        refund_id = f"rfnd_{len(self._refunds) + 1:05d}"
        result = RazorpayRefundResult(
            id=refund_id,
            status="processed",
            amount=amount_paise,
            raw={
                "id": refund_id,
                "payment_id": payment_id,
                "amount": amount_paise,
                "notes": notes or {},
            },
        )
        self._refunds.append(result)
        return result

    def verify_webhook_signature(self, body: bytes, signature: str | None) -> None:
        # Always accept in tests
        return


def serialize_headers(headers: Dict[str, str]) -> str:
    """Serialize webhook headers into a deterministic JSON string."""

    return json.dumps({k: v for k, v in headers.items()}, sort_keys=True)
