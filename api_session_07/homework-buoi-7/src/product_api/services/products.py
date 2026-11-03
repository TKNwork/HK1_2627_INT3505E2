from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from product_api.extensions import db
from product_api.models import Product
from product_api.errors import ApiError


def active_product(product_id):
    product = db.session.scalar(select(Product).where(Product.id == product_id, Product.archived.is_(False)))
    if product is None:
        raise ApiError(404, "product_not_found", "Active product not found.")
    return product


def commit_product():
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        original = exc.orig
        constraint = getattr(getattr(original, "diag", None), "constraint_name", None)
        sqlite_duplicate = (getattr(original, "sqlite_errorname", None) == "SQLITE_CONSTRAINT_UNIQUE"
                            and "products.sku" in str(original))
        if constraint == "uq_products_sku" or sqlite_duplicate:
            raise ApiError(409, "duplicate_sku", "SKU already exists, including archived products.") from exc
        raise


def create_product(data):
    product = Product(**data)
    db.session.add(product)
    commit_product()
    return product


def reserve_product(product_id, qty):
    # One conditional UPDATE: the database atomically checks and decrements stock.
    row = db.session.execute(update(Product).where(
        Product.id == product_id, Product.archived.is_(False), Product.qty_in_stock >= qty
    ).values(qty_in_stock=Product.qty_in_stock - qty).returning(Product.id)).scalar_one_or_none()
    if row is None:
        active_product(product_id)
        raise ApiError(409, "insufficient_stock", "Insufficient stock.")
    db.session.commit()
    return active_product(product_id)
