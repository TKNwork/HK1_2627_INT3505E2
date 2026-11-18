from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from product_api.extensions import db
from product_api.models import Product, Order, OrderItem
from product_api.errors import ApiError


def order_query():
    return select(Order).options(selectinload(Order.items).joinedload(OrderItem.product))


def get_order(order_id):
    order = db.session.scalar(order_query().where(Order.id == order_id))
    if order is None:
        raise ApiError(404, "order_not_found", "Order not found.")
    return order


def create_order(data):
    try:
        ids = [item["product_id"] for item in data["items"]]
        # PostgreSQL shared locks keep prices/archive status stable until commit.
        products = db.session.scalars(select(Product).where(
            Product.id.in_(ids), Product.archived.is_(False)).order_by(Product.id).with_for_update(read=True)).all()
        by_id = {product.id: product for product in products}
        if len(by_id) != len(ids):
            raise ApiError(404, "product_not_found", "An active product in the order was not found.")
        order = Order(items=[OrderItem(product=by_id[item["product_id"]],
            quantity=item["quantity"], unit_price_cents=by_id[item["product_id"]].price_cents)
            for item in data["items"]])
        db.session.add(order)
        db.session.flush()
        order_id = order.id
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return get_order(order_id)
