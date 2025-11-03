from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from typing import Any, cast

import pytest  # type: ignore[import-not-found]
from fastapi.testclient import TestClient  # type: ignore[import-not-found]
import urllib.request

from app.api.deps import notification_dispatcher
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.main import app
from app.repositories import invoices as invoice_repo
from app.services.notifications import NotificationService
from app.services.workflows import SQSNotificationDispatcher
from app.workers import order_paid as order_paid_worker

from tests.test_orders_routes import _create_cake, _create_cart


class StubSQSClient:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    def send_message(
        self, QueueUrl: str, MessageBody: str, MessageAttributes: dict[str, object]
    ) -> dict[str, str]:
        self.messages.append(
            {
                "QueueUrl": QueueUrl,
                "MessageBody": MessageBody,
                "MessageAttributes": MessageAttributes,
            }
        )
        return {"MessageId": "stub-message-id"}


class FakeS3Client:
    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []

    def put_object(
        self, Bucket: str, Key: str, Body: bytes, ContentType: str
    ) -> dict[str, object]:
        self.put_calls.append(
            {
                "Bucket": Bucket,
                "Key": Key,
                "Body": Body,
                "ContentType": ContentType,
            }
        )
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


class FakeBoto3Module:
    def __init__(self, s3_client: FakeS3Client) -> None:
        self._s3_client = s3_client

    def client(self, service_name: str, *_args, **_kwargs) -> FakeS3Client:
        if service_name != "s3":
            raise AssertionError(f"Unexpected service {service_name!r} requested")
        return self._s3_client


class FakeSNSClient:
    def __init__(self) -> None:
        self.published: list[dict[str, object]] = []

    def publish(self, **kwargs) -> dict[str, str]:
        self.published.append(kwargs)
        return {"MessageId": "sns-message-id"}


class FakeSecretsClient:
    def __init__(self, secret_string: str) -> None:
        self._secret_string = secret_string

    def get_secret_value(self, SecretId: str) -> dict[str, str]:
        return {"SecretString": self._secret_string}


def _messages_of_type(
    stub_sqs: StubSQSClient, message_type: str
) -> list[tuple[str, dict[str, Any]]]:
    results: list[tuple[str, dict[str, Any]]] = []
    for message in stub_sqs.messages:
        raw_body = cast(str, message["MessageBody"])
        parsed = json.loads(raw_body)
        if parsed.get("type") == message_type:
            results.append((raw_body, parsed))
    return results


def test_payment_webhook_triggers_invoice_pipeline(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue_url = "https://sqs.local/queues/order-paid"
    stub_sqs = StubSQSClient()
    app.dependency_overrides[
        notification_dispatcher
    ] = lambda: SQSNotificationDispatcher(queue_url, client=stub_sqs)
    try:
        cake_id = _create_cake(client, admin_headers)
        customer_id = str(uuid.uuid4())
        cart_id = _create_cart(client, cake_id, customer_id)
        idem_key = str(uuid.uuid4())
        create_resp = client.post(
            "/api/v1/orders",
            json={
                "idempotency_key": idem_key,
                "cart_id": cart_id,
                "customer_id": customer_id,
                "is_test": False,
            },
        )
        assert create_resp.status_code == 200
        order_payload = create_resp.json()
        order_id = order_payload["order"]["order_id"]
        provider_order_id = order_payload["provider_order_id"]

        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_capture_test",
                        "status": "captured",
                        "order_id": provider_order_id,
                    }
                }
            },
        }
        webhook_resp = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=webhook_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert webhook_resp.status_code == 200

        assert len(stub_sqs.messages) >= 1
        order_paid_messages = _messages_of_type(stub_sqs, "order.paid")

        assert len(order_paid_messages) == 1
        message_body, body_payload = order_paid_messages[0]
        assert body_payload["payload"]["order_id"] == order_id

        fake_s3 = FakeS3Client()
        monkeypatch.setattr(
            "app.services.invoices.boto3",
            FakeBoto3Module(fake_s3),
            raising=False,
        )

        first_result = order_paid_worker.handle({"Records": [{"body": message_body}]})
        assert first_result["processed"] == 1
        assert first_result["errors"] == []
        assert len(fake_s3.put_calls) == 1

        second_result = order_paid_worker.handle({"Records": [{"body": message_body}]})
        assert second_result["processed"] == 1
        assert second_result["errors"] == []
        assert len(fake_s3.put_calls) == 1

        settings = get_settings()
        session_iter = get_db_session(settings.database_url)
        session = next(session_iter)
        try:
            invoice = invoice_repo.get_latest_invoice_for_order(session, order_id)
        finally:
            try:
                next(session_iter)
            except StopIteration:
                pass
        assert invoice.s3_key == fake_s3.put_calls[0]["Key"]
    finally:
        app.dependency_overrides.pop(notification_dispatcher, None)


def test_duplicate_payment_webhook_is_idempotent(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    queue_url = "https://sqs.local/queues/order-paid"
    stub_sqs = StubSQSClient()
    app.dependency_overrides[
        notification_dispatcher
    ] = lambda: SQSNotificationDispatcher(queue_url, client=stub_sqs)
    try:
        cake_id = _create_cake(client, admin_headers)
        customer_id = str(uuid.uuid4())
        cart_id = _create_cart(client, cake_id, customer_id)
        idem_key = str(uuid.uuid4())

        create_resp = client.post(
            "/api/v1/orders",
            json={
                "idempotency_key": idem_key,
                "cart_id": cart_id,
                "customer_id": customer_id,
                "is_test": False,
            },
        )
        assert create_resp.status_code == 200
        order_payload = create_resp.json()
        order_id = order_payload["order"]["order_id"]
        provider_order_id = order_payload["provider_order_id"]

        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_capture_duplicate",
                        "status": "captured",
                        "order_id": provider_order_id,
                    }
                }
            },
        }

        first_response = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=webhook_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert first_response.status_code == 200

        order_paid_messages = _messages_of_type(stub_sqs, "order.paid")
        assert len(order_paid_messages) == 1
        first_detail = client.get(f"/api/v1/orders/{order_id}")
        assert first_detail.status_code == 200
        first_order_state = first_detail.json()["order"]
        assert first_order_state["payment_status"] in {"paid", "authorized"}

        second_response = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=webhook_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert second_response.status_code == 200

        order_paid_messages = _messages_of_type(stub_sqs, "order.paid")
        assert (
            len(order_paid_messages) == 1
        ), "duplicate webhook emitted a second order.paid message"
        second_detail = client.get(f"/api/v1/orders/{order_id}")
        assert second_detail.status_code == 200
        second_order_state = second_detail.json()["order"]
        assert (
            second_order_state["payment_status"] == first_order_state["payment_status"]
        )
        assert second_order_state["provider_payment_id"] == "pay_capture_duplicate"
    finally:
        app.dependency_overrides.pop(notification_dispatcher, None)


def test_refund_webhook_updates_state_and_is_idempotent(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    queue_url = "https://sqs.local/queues/order-paid"
    stub_sqs = StubSQSClient()
    app.dependency_overrides[
        notification_dispatcher
    ] = lambda: SQSNotificationDispatcher(queue_url, client=stub_sqs)
    try:
        cake_id = _create_cake(client, admin_headers)
        customer_id = str(uuid.uuid4())
        cart_id = _create_cart(client, cake_id, customer_id)

        create_resp = client.post(
            "/api/v1/orders",
            json={
                "idempotency_key": str(uuid.uuid4()),
                "cart_id": cart_id,
                "customer_id": customer_id,
                "is_test": False,
            },
        )
        assert create_resp.status_code == 200
        order_payload = create_resp.json()
        order_id = order_payload["order"]["order_id"]
        provider_order_id = order_payload["provider_order_id"]

        capture_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_capture_for_refund",
                        "status": "captured",
                        "order_id": provider_order_id,
                    }
                }
            },
        }
        capture_resp = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=capture_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert capture_resp.status_code == 200
        order_paid_messages = _messages_of_type(stub_sqs, "order.paid")
        assert len(order_paid_messages) == 1

        detail_after_capture = client.get(f"/api/v1/orders/{order_id}")
        assert detail_after_capture.status_code == 200
        captured_state = detail_after_capture.json()["order"]
        provider_payment_id = captured_state["provider_payment_id"]
        assert provider_payment_id == "pay_capture_for_refund"

        refund_payload = {
            "event": "refund.processed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": provider_payment_id,
                        "status": "refunded",
                        "order_id": provider_order_id,
                    }
                }
            },
        }
        first_refund_resp = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=refund_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert first_refund_resp.status_code == 200

        detail_after_refund = client.get(f"/api/v1/orders/{order_id}")
        assert detail_after_refund.status_code == 200
        refund_state = detail_after_refund.json()["order"]
        assert refund_state["status"] == "refunded"
        assert refund_state["payment_status"] == "refunded"
        assert refund_state["inventory_released"] is True
        order_paid_messages = _messages_of_type(stub_sqs, "order.paid")
        assert len(order_paid_messages) == 1
        order_refunded_messages = _messages_of_type(stub_sqs, "order.refunded")
        assert len(order_refunded_messages) == 1

        second_refund_resp = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=refund_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert second_refund_resp.status_code == 200

        detail_after_duplicate_refund = client.get(f"/api/v1/orders/{order_id}")
        assert detail_after_duplicate_refund.status_code == 200
        duplicate_state = detail_after_duplicate_refund.json()["order"]
        assert duplicate_state["status"] == "refunded"
        assert duplicate_state["payment_status"] == "refunded"
        order_paid_messages = _messages_of_type(stub_sqs, "order.paid")
        assert len(order_paid_messages) == 1
        order_refunded_messages = _messages_of_type(stub_sqs, "order.refunded")
        assert len(order_refunded_messages) == 1
    finally:
        app.dependency_overrides.pop(notification_dispatcher, None)


def test_payment_failure_webhook_emits_notification(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    queue_url = "https://sqs.local/queues/order-paid"
    stub_sqs = StubSQSClient()
    app.dependency_overrides[
        notification_dispatcher
    ] = lambda: SQSNotificationDispatcher(queue_url, client=stub_sqs)
    try:
        cake_id = _create_cake(client, admin_headers)
        customer_id = str(uuid.uuid4())
        cart_id = _create_cart(client, cake_id, customer_id)
        create_resp = client.post(
            "/api/v1/orders",
            json={
                "idempotency_key": str(uuid.uuid4()),
                "cart_id": cart_id,
                "customer_id": customer_id,
                "is_test": False,
            },
        )
        assert create_resp.status_code == 200
        order_payload = create_resp.json()
        order_id = order_payload["order"]["order_id"]
        provider_order_id = order_payload["provider_order_id"]

        failure_payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_failed_test",
                        "status": "failed",
                        "order_id": provider_order_id,
                    }
                }
            },
        }
        first_failure_resp = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=failure_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert first_failure_resp.status_code == 200

        detail_after_failure = client.get(f"/api/v1/orders/{order_id}")
        assert detail_after_failure.status_code == 200
        failed_state = detail_after_failure.json()["order"]
        assert failed_state["status"] == "payment_failed"
        assert failed_state["payment_status"] == "failed"
        order_failed_messages = _messages_of_type(stub_sqs, "order.payment_failed")
        assert len(order_failed_messages) == 1

        second_failure_resp = client.post(
            "/api/v1/orders/payments/webhook/razorpay",
            json=failure_payload,
            headers={"X-Razorpay-Signature": "stub"},
        )
        assert second_failure_resp.status_code == 200

        order_failed_messages = _messages_of_type(stub_sqs, "order.payment_failed")
        assert len(order_failed_messages) == 1
    finally:
        app.dependency_overrides.pop(notification_dispatcher, None)


def test_notification_service_dispatches_multiple_channels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sns_client = FakeSNSClient()
    secrets_client = FakeSecretsClient(
        json.dumps({"access_token": "whatsapp-test-token"})
    )
    monkeypatch.setenv(
        "ADMIN_NOTIFICATIONS_TOPIC_ARN", "arn:aws:sns:local:123456:order-paid"
    )
    monkeypatch.setenv(
        "WHATSAPP_SECRET_ARN", "arn:aws:secretsmanager:local:secret/whatsapp"
    )
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "1234567890")
    monkeypatch.setenv("WHATSAPP_DEFAULT_RECIPIENT", "919999999999")
    monkeypatch.setenv("S3_BUCKET_INVOICES", "test-invoices")
    settings = Settings()
    captured_requests: list[urllib.request.Request] = []

    class _DummyResponse:
        def __enter__(self) -> "_DummyResponse":
            return self

        def __exit__(self, *_exc) -> bool:
            return False

    def fake_urlopen(request: urllib.request.Request, timeout: int = 10):
        captured_requests.append(request)
        return _DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    service = NotificationService(
        settings,
        sns_client=sns_client,
        secrets_client=secrets_client,
    )
    assert service._whatsapp is not None

    order = SimpleNamespace(
        order_id="order_test_001",
        customer_id="cust_123",
        total=1999.0,
        currency="INR",
        status="confirmed",
        payment_status="paid",
        is_test=False,
    )
    invoice = SimpleNamespace(s3_bucket="bucket", s3_key="invoices/order_test_001.json")

    service.notify_order_paid(order, invoice)

    assert len(sns_client.published) == 1
    sns_payload = sns_client.published[0]
    assert sns_payload["TopicArn"] == settings.admin_notifications_topic_arn
    message_body = json.loads(cast(str, sns_payload["Message"]))
    assert message_body["order_id"] == order.order_id
    assert (
        message_body["invoice_location"] == "s3://bucket/invoices/order_test_001.json"
    )

    assert len(captured_requests) == 1
    request_body = cast(bytes, captured_requests[0].data)
    whatsapp_payload = json.loads(request_body.decode("utf-8"))
    whatsapp_message = whatsapp_payload["text"]["body"]
    assert order.order_id in whatsapp_message
    assert "Invoice" in whatsapp_message

    service.notify_order_refunded(order)
    service.notify_payment_failed(order)

    assert len(sns_client.published) == 3
    events = [
        cast(dict[str, Any], entry["MessageAttributes"])["event"]["StringValue"]
        for entry in sns_client.published
    ]
    assert events == [
        "order.paid",
        "order.refunded",
        "order.payment_failed",
    ]
