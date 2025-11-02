from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(admin_headers: dict[str, str]) -> dict[str, str]:
    return admin_headers.copy()


def test_cake_admin_flow(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_payload = {
        "name": "Belgian Chocolate",
        "slug": "belgian-chocolate",
        "description": "Rich chocolate icing",
        "price": 1499.0,
        "currency": "INR",
        "category": "signature",
        "is_available": True,
        "stock_quantity": 5,
        "image_url": "https://example.com/choco.jpg",
    }

    create_resp = client.post(
        "/api/v1/admin/cakes", json=create_payload, headers=_headers(admin_headers)
    )
    assert create_resp.status_code == 200
    body = create_resp.json()
    cake_id = body["cake"]["cake_id"]
    assert body["cake"]["slug"] == "belgian-chocolate"
    assert body["request"]["request_id"]

    update_resp = client.patch(
        f"/api/v1/admin/cakes/{cake_id}",
        json={"price": 1599.0, "stock_quantity": 7},
        headers=_headers(admin_headers),
    )
    assert update_resp.status_code == 200, update_resp.json()
    updated = update_resp.json()
    assert updated["cake"]["price"] == 1599.0
    assert updated["cake"]["stock_quantity"] == 7

    availability_resp = client.patch(
        f"/api/v1/admin/cakes/{cake_id}/availability",
        json={"is_available": False},
        headers=_headers(admin_headers),
    )
    assert availability_resp.status_code == 200
    assert availability_resp.json()["cake"]["is_available"] is False

    inventory_resp = client.post(
        f"/api/v1/admin/cakes/{cake_id}/inventory",
        json={"delta": -2},
        headers=_headers(admin_headers),
    )
    assert inventory_resp.status_code == 200
    assert inventory_resp.json()["cake"]["stock_quantity"] == 5

    publish_resp = client.post(
        f"/api/v1/admin/cakes/{cake_id}/publish", headers=_headers(admin_headers)
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["success"] is True


def test_duplicate_slug_rejected(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    payload = {
        "name": "Red Velvet",
        "slug": "red-velvet",
        "description": None,
        "price": 1299.0,
        "currency": "INR",
        "category": None,
        "is_available": True,
        "stock_quantity": 3,
        "image_url": None,
    }
    first = client.post(
        "/api/v1/admin/cakes", json=payload, headers=_headers(admin_headers)
    )
    assert first.status_code == 200
    dup = client.post(
        "/api/v1/admin/cakes", json=payload, headers=_headers(admin_headers)
    )
    assert dup.status_code == 409
    assert dup.json()["detail"]["code"] == "cake_slug_conflict"


def test_negative_inventory_returns_error(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    payload = {
        "name": "Cheesecake",
        "slug": "cheesecake",
        "description": None,
        "price": 999.0,
        "currency": "INR",
        "category": None,
        "is_available": True,
        "stock_quantity": 1,
        "image_url": None,
    }
    resp = client.post(
        "/api/v1/admin/cakes", json=payload, headers=_headers(admin_headers)
    )
    cake_id = resp.json()["cake"]["cake_id"]

    invalid = client.post(
        f"/api/v1/admin/cakes/{cake_id}/inventory",
        json={"delta": -5},
        headers=_headers(admin_headers),
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"]["code"] == "inventory_adjustment_invalid"


def test_missing_admin_token_returns_unauthorized(client: TestClient) -> None:
    payload = {
        "name": "Lemon Tart",
        "slug": "lemon-tart",
        "description": None,
        "price": 899.0,
        "currency": "INR",
        "category": None,
        "is_available": True,
        "stock_quantity": 2,
        "image_url": None,
    }
    resp = client.post("/api/v1/admin/cakes", json=payload)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "unauthorized"
