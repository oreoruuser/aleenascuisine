from __future__ import annotations

from fastapi.testclient import TestClient


def _create_cake(
    client: TestClient, admin_headers: dict[str, str], slug: str
) -> dict[str, str]:
    payload = {
        "name": slug.title(),
        "slug": slug,
        "description": None,
        "price": 499.0,
        "currency": "INR",
        "category": "classic",
        "is_available": True,
        "stock_quantity": 20,
        "image_url": None,
    }
    resp = client.post("/api/v1/admin/cakes", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    return {"cake_id": data["cake"]["cake_id"], "name": payload["name"]}


def test_cart_crud_flow(client: TestClient, admin_headers: dict[str, str]) -> None:
    cake = _create_cake(client, admin_headers, "vanilla")
    cart_payload = {
        "customer_id": "cust-123",
        "cart_token": "token-xyz",
        "items": [
            {"cake_id": cake["cake_id"], "quantity": 2, "price_each": 499.0},
        ],
    }

    upsert_resp = client.post("/api/v1/cart", json=cart_payload)
    assert upsert_resp.status_code == 200
    cart_body = upsert_resp.json()
    cart_id = cart_body["cart_id"]
    assert cart_body["cart_token"] == "token-xyz"
    assert cart_body["totals"]["total"] == 998.0

    get_by_id = client.get(f"/api/v1/cart/{cart_id}")
    assert get_by_id.status_code == 200
    assert get_by_id.json()["cart_id"] == cart_id

    get_by_token = client.get("/api/v1/cart/token-xyz")
    assert get_by_token.status_code == 200
    assert get_by_token.json()["cart_id"] == cart_id

    delete_resp = client.delete(f"/api/v1/cart/{cart_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing = client.get(f"/api/v1/cart/{cart_id}")
    assert missing.status_code == 404
