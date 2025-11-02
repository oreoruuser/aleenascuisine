from __future__ import annotations

from fastapi.testclient import TestClient


def _create_cake(
    client: TestClient,
    admin_headers: dict[str, str],
    slug: str,
    name: str,
    price: float,
) -> str:
    payload = {
        "name": name,
        "slug": slug,
        "description": f"Description for {name}",
        "price": price,
        "currency": "INR",
        "category": "featured",
        "is_available": True,
        "stock_quantity": 10,
        "image_url": "https://example.com/image.jpg",
    }
    resp = client.post("/api/v1/admin/cakes", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    return resp.json()["cake"]["cake_id"]


def test_list_and_get_cakes(client: TestClient, admin_headers: dict[str, str]) -> None:
    cake_a = _create_cake(client, admin_headers, "truffle", "Truffle", 899.0)
    cake_b = _create_cake(client, admin_headers, "choco-chip", "Choco Chip", 799.0)

    listing = client.get("/api/v1/cakes")
    body = listing.json()
    assert listing.status_code == 200
    assert body["total_count"] >= 2
    assert any(item["cake_id"] == cake_a for item in body["cakes"])

    filtered = client.get("/api/v1/cakes", params={"search": "truffle"})
    assert filtered.status_code == 200
    assert filtered.json()["cakes"][0]["slug"] == "truffle"

    detail_resp = client.get(f"/api/v1/cakes/{cake_b}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["cake"]["cake_id"] == cake_b
