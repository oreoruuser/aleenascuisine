from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def _create_cake(client: TestClient, admin_headers: dict[str, str]) -> str:
    slug = f"cake-{uuid.uuid4().hex[:6]}"
    payload = {
        "name": "Special Cake",
        "slug": slug,
        "description": None,
        "price": 1199.0,
        "currency": "INR",
        "category": "premium",
        "is_available": True,
        "stock_quantity": 15,
        "image_url": None,
    }
    resp = client.post("/api/v1/admin/cakes", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    return resp.json()["cake"]["cake_id"]


def _create_cart(client: TestClient, cake_id: str, customer_id: str) -> str:
    payload = {
        "customer_id": customer_id,
        "cart_token": None,
        "items": [
            {"cake_id": cake_id, "quantity": 1, "price_each": 1199.0},
        ],
    }
    resp = client.post("/api/v1/cart", json=payload)
    assert resp.status_code == 200
    return resp.json()["cart_id"]


def test_order_lifecycle(client: TestClient, admin_headers: dict[str, str]) -> None:
    cake_id = _create_cake(client, admin_headers)
    customer_id = str(uuid.uuid4())
    cart_id = _create_cart(client, cake_id, customer_id)
    idem_key = str(uuid.uuid4())

    create_payload = {
        "idempotency_key": idem_key,
        "cart_id": cart_id,
        "customer_id": customer_id,
        "is_test": False,
    }
    create_resp = client.post("/api/v1/orders", json=create_payload)
    assert create_resp.status_code == 200
    order_body = create_resp.json()
    order_id = order_body["order"]["order_id"]
    provider_order_id = order_body["provider_order_id"]
    assert provider_order_id
    payment_id = order_body["order"].get("payment_id")
    assert payment_id

    # Idempotency should return same order ID
    repeat_resp = client.post("/api/v1/orders", json=create_payload)
    assert repeat_resp.status_code == 200
    assert repeat_resp.json()["order"]["order_id"] == order_id

    list_resp = client.get(f"/api/v1/orders/{customer_id}")
    assert list_resp.status_code == 200
    list_payload = list_resp.json()
    assert list_payload["orders"][0]["order_id"] == order_id
    assert list_payload["orders"][0]["items"]
    assert list_payload["orders"][0]["payment_status"] == "pending"

    detail_resp = client.get(f"/api/v1/orders/{order_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["order"]["order_id"] == order_id

    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_stub_001",
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
    assert webhook_resp.json()["accepted"] is True

    detail_after_webhook = client.get(f"/api/v1/orders/{order_id}")
    assert detail_after_webhook.status_code == 200
    assert detail_after_webhook.json()["order"]["payment_status"] in {
        "paid",
        "authorized",
    }

    cancel_resp = client.post(f"/api/v1/orders/{order_id}/cancel")
    assert cancel_resp.status_code == 200
    cancel_body = cancel_resp.json()
    assert cancel_body["order"]["status"] == "cancelled"

    refund_resp = client.post(
        "/api/v1/orders/payments/refund",
        json={
            "payment_id": payment_id,
            "amount": 500.0,
            "reason": "customer request",
        },
        headers=admin_headers,
    )
    assert refund_resp.status_code == 200
    refund_body = refund_resp.json()
    assert refund_body["status"] in {"requested", "processed", "completed", "success"}


def test_order_price_mismatch(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    cake_id = _create_cake(client, admin_headers)
    customer_id = str(uuid.uuid4())
    payload = {
        "customer_id": customer_id,
        "cart_token": None,
        "items": [
            {"cake_id": cake_id, "quantity": 1, "price_each": 999.0},
        ],
    }
    cart_resp = client.post("/api/v1/cart", json=payload)
    assert cart_resp.status_code == 200
    cart_id = cart_resp.json()["cart_id"]

    create_resp = client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": str(uuid.uuid4()),
            "cart_id": cart_id,
            "customer_id": customer_id,
        },
    )
    assert create_resp.status_code == 409
    body = create_resp.json()
    assert body["detail"]["code"] == "cart_price_mismatch"
    items = body["detail"]["details"]["items"]
    assert items and items[0]["cake_id"] == cake_id


def test_payment_failure_releases_inventory(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    cake_id = _create_cake(client, admin_headers)
    customer_id = str(uuid.uuid4())
    cart_id = _create_cart(client, cake_id, customer_id)
    create_resp = client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": str(uuid.uuid4()),
            "cart_id": cart_id,
            "customer_id": customer_id,
        },
    )
    assert create_resp.status_code == 200
    order_payload = create_resp.json()
    order_id = order_payload["order"]["order_id"]
    provider_order_id = order_payload["provider_order_id"]

    webhook_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_001",
                    "status": "failed",
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

    detail_resp = client.get(f"/api/v1/orders/{order_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["order"]
    assert detail["status"] == "payment_failed"
    assert detail["inventory_released"] is True
    assert detail["reservation_expires_at"] is None
