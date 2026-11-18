from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from product_api.extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_products_sku"),
        CheckConstraint("price_cents >= 0", name="ck_products_price"),
        CheckConstraint("qty_in_stock >= 0", name="ck_products_stock"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(nullable=False)
    qty_in_stock: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    archived: Mapped[bool] = mapped_column(default=False, server_default="false", index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product", lazy="raise")
