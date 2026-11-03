import pytest
from flask_migrate import upgrade
from product_api import create_app
from product_api.extensions import db
from pathlib import Path

@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"), "LOG_LEVEL": "ERROR"})
    with app.app_context():
        upgrade(directory=str(Path(__file__).resolve().parents[1] / "migrations"))
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def make_product(client):
    def make(sku="SKU-001", **changes):
        data = dict(sku=sku, name="Keyboard", price_cents=12500, qty_in_stock=10)
        data.update(changes)
        response = client.post("/api/v1/products", json=data)
        assert response.status_code == 201, response.json
        return response.json
    return make
