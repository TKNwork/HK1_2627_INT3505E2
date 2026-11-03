import pytest
from sqlalchemy import event, select, func
from product_api.extensions import db
from product_api.models import Order, OrderItem

BASE = "/api/v1/orders"

def test_create_order_snapshot(client, make_product):
    a, b = make_product("AAA"), make_product("BBB", price_cents=300)
    body = {"items": [{"product_id": a["id"], "quantity": 2}, {"product_id": b["id"], "quantity": 3}]}
    response = client.post(BASE, json=body)
    assert response.status_code == 201
    order = response.json
    assert len(order["items"]) == 2 and order["total_cents"] == 25900
    assert client.get(f"/api/v1/products/{a['id']}").json["qty_in_stock"] == 10
    client.patch(f"/api/v1/products/{a['id']}", json={"price_cents": 7})
    client.delete(f"/api/v1/products/{a['id']}")
    result = client.get(f"{BASE}/{order['id']}").json
    assert result["items"][0]["unit_price_cents"] == 12500
    assert result["items"][0]["product"]["price_cents"] == 7
    assert result["items"][0]["product"]["archived"] is True
    assert result["total_cents"] == 25900
    assert client.get(BASE + "/99999").status_code == 404

@pytest.mark.parametrize("body", [
    {"items": []}, {}, {"items": [{"product_id": 1, "quantity": True}]},
    {"items": [{"product_id": 1, "quantity": 0}]},
    {"items": [{"product_id": 1, "quantity": 1, "unit_price_cents": 1}]},
    {"items": [{"product_id": 1, "quantity": 1}] * 2},
    {"items": [{"product_id": 1, "quantity": 1}] * 101},
])
def test_order_validation(client, body):
    assert client.post(BASE, json=body).status_code == 422

def test_order_invalid_item_atomic(app, client, make_product):
    p = make_product()
    body = {"items": [{"product_id": p["id"], "quantity": 1}, {"product_id": 999999, "quantity": 1}]}
    assert client.post(BASE, json=body).status_code == 404
    client.delete(f"/api/v1/products/{p['id']}")
    assert client.post(BASE, json={"items": [{"product_id": p["id"], "quantity": 1}]}).status_code == 404
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(Order)) == 0
        assert db.session.scalar(select(func.count()).select_from(OrderItem)) == 0

def test_order_write_failure_rolls_back(app, client, make_product):
    p = make_product()
    def fail(mapper, connection, target):
        raise RuntimeError("simulated item insert failure")
    event.listen(OrderItem, "before_insert", fail)
    try:
        assert client.post(BASE, json={"items": [{"product_id": p["id"], "quantity": 1}]}).status_code == 500
    finally:
        event.remove(OrderItem, "before_insert", fail)
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(Order)) == 0
        assert db.session.scalar(select(func.count()).select_from(OrderItem)) == 0

def test_orders_eager_query_count(app, client, make_product):
    products = [make_product(f"SKU-{i}") for i in range(3)]
    def seed(n):
        for _ in range(n):
            assert client.post(BASE, json={"items": [{"product_id": p["id"], "quantity": 2} for p in products]}).status_code == 201
    seed(2)
    def measure(url):
        statements = []
        def count(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)
        with app.app_context():
            db.session.remove()  # Fresh identity map; fixtures cannot hide lazy loading.
            engine = db.engine
            event.listen(engine, "before_cursor_execute", count)
            try:
                response = client.get(url)
                assert response.status_code == 200
                assert all(len(order["items"]) == 3 for order in response.json.get("items", []) if "items" in order)
            finally:
                event.remove(engine, "before_cursor_execute", count)
                db.session.remove()
        return response.json, statements
    data, small = measure(BASE)
    assert len(small) == 3  # COUNT + page of Orders + items JOIN current Products.
    seed(6)
    data, large = measure(BASE)
    assert data["total"] == 8 and len(data["items"]) == 8
    assert len(large) == len(small) == 3
    detail, detail_queries = measure(f"{BASE}/{data['items'][0]['id']}")
    assert len(detail_queries) == 2
    page = client.get(BASE + "?page=2&size=3").json
    assert page["total"] == 8 and len(page["items"]) == 3
    assert client.get(BASE + "?page=999").json["items"] == []
