import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from product_api.extensions import db


def test_migration_structure_and_foreign_keys(app):
    with app.app_context():
        inspector = inspect(db.engine)
        assert set(inspector.get_table_names()) == {"products", "orders", "order_items", "alembic_version"}
        assert db.session.scalar(text("PRAGMA foreign_keys")) == 1
        assert len(inspector.get_foreign_keys("order_items")) == 2
        assert {index["name"] for index in inspector.get_indexes("order_items")} == {
            "ix_order_items_order_id", "ix_order_items_product_id"}
        assert {constraint["name"] for constraint in inspector.get_check_constraints("products")} == {
            "ck_products_price", "ck_products_stock"}


@pytest.mark.parametrize("statement", [
    "INSERT INTO products (sku,name,price_cents,qty_in_stock,created_at,updated_at) VALUES ('ABC','x',-1,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
    "INSERT INTO products (sku,name,price_cents,qty_in_stock,created_at,updated_at) VALUES ('ABC','x',1,-1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
    "INSERT INTO order_items (order_id,product_id,quantity,unit_price_cents) VALUES (999,999,1,1)",
])
def test_database_rejects_invalid_direct_writes(app, statement):
    with app.app_context():
        with pytest.raises(IntegrityError):
            db.session.execute(text(statement))
            db.session.commit()
        db.session.rollback()
        assert db.session.scalar(text("SELECT count(*) FROM order_items")) == 0
