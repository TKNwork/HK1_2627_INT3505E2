import pytest
from sqlalchemy import select
from product_api.extensions import db
from product_api.models import Product

BASE = "/api/v1/products"

def test_create_and_duplicate(app, client, make_product):
    p = make_product(sku="  abc-123  ", name="  Keyboard  ")
    assert p["sku"] == "ABC-123" and p["name"] == "Keyboard"
    with app.app_context():
        assert db.session.scalar(select(Product)).id == p["id"]
    response = client.post(BASE, json=dict(sku="abc-123", name="x", price_cents=1))
    assert response.status_code == 409
    assert response.json["error"] == "duplicate_sku"
    make_product("SECOND")  # A failed transaction does not poison later requests.

@pytest.mark.parametrize("change", [
    {"price_cents": -1}, {"price_cents": True}, {"price_cents": 1.5},
    {"price_cents": "2"}, {"price_cents": 2147483648}, {"qty_in_stock": -1},
    {"name": "   "}, {"sku": "xx"}, {"sku": "a b"}, {"id": 3},
    {"archived": True}, {"created_at": "2026-01-01"}, {"unknown": 1},
    {"description": "x" * 4001}, {"name": None},
])
def test_invalid_product(client, change):
    data = dict(sku="ABC", name="name", price_cents=1)
    data.update(change)
    response = client.post(BASE, json=data)
    assert response.status_code == 422
    assert response.json["error"] == "validation_error"
    assert "fields" in response.json

@pytest.mark.parametrize("body", [[], None, True, 1, "x"])
def test_wrong_json_shape(client, body):
    import json
    assert client.post(BASE, data=json.dumps(body), content_type="application/json").status_code == 422

def test_protocol_errors(client):
    assert client.post(BASE, data="{", content_type="application/json").status_code == 400
    assert client.post(BASE, data="{}").status_code == 415
    response = client.put(BASE, json={})
    assert response.status_code == 405 and "Allow" in response.headers
    assert client.get("/missing").json["error"] == "not_found"

@pytest.mark.parametrize("query", ["page=0", "page=-1", "page=no", "page=1.5", "size=101", "size=0", "size=bad", "extra=1"])
def test_bad_pagination(client, query):
    assert client.get(BASE + "?" + query).status_code == 422

def test_pagination_patch_soft_delete(client, make_product):
    a, b, c = [make_product(f"SKU-{i}") for i in range(3)]
    response = client.patch(f"{BASE}/{a['id']}", json={"name": " New "})
    assert response.status_code == 200
    assert response.json["name"] == "New"
    assert response.json["qty_in_stock"] == 10
    assert client.patch(f"{BASE}/{a['id']}", json={}).status_code == 422
    assert client.patch(f"{BASE}/{a['id']}", json={"archived": True}).status_code == 422
    assert client.patch(f"{BASE}/{a['id']}", json={"sku": b["sku"]}).status_code == 409
    deleted = client.delete(f"{BASE}/{a['id']}")
    assert deleted.status_code == 204 and deleted.data == b""
    for method, suffix, data in [("get", "", None), ("delete", "", None), ("patch", "", {"name": "x"}), ("post", "/reserve", {"qty": 1})]:
        assert getattr(client, method)(f"{BASE}/{a['id']}" + suffix, json=data).status_code == 404
    result = client.get(BASE + "?size=1&page=2").json
    assert result["total"] == 2 and result["items"][0]["id"] == c["id"]
    assert client.get(BASE + "?page=999").json["items"] == []
    assert client.get(BASE + "/99999").status_code == 404

def test_reserve(client, make_product):
    p = make_product()
    url = f"{BASE}/{p['id']}/reserve"
    assert client.post(url, json={"qty": 3}).json["qty_in_stock"] == 7
    assert client.post(url, json={"qty": 8}).status_code == 409
    assert client.get(f"{BASE}/{p['id']}").json["qty_in_stock"] == 7
    assert client.post(url, json={"qty": 7}).json["qty_in_stock"] == 0
    assert client.post(url, json={"qty": 1}).status_code == 409

@pytest.mark.parametrize("qty", [0, -1, True, False, "1", 1.5, None, 2147483648])
def test_invalid_reserve(client, make_product, qty):
    p = make_product()
    assert client.post(f"{BASE}/{p['id']}/reserve", json={"qty": qty}).status_code == 422

def test_unknown_constraint_is_not_duplicate(app, client, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    def fail():
        raise IntegrityError("hidden SQL", {}, Exception("secret database detail"))
    monkeypatch.setattr(db.session, "commit", fail)
    response = client.post(BASE, json={"sku": "ABC", "name": "x", "price_cents": 1})
    assert response.status_code == 500
    assert response.json["error"] == "internal_error"
    assert "secret" not in response.text and "SQL" not in response.text
