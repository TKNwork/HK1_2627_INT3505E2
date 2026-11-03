from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import select, func
from product_api.extensions import db
from product_api.models import Product
from product_api.schemas.product import ProductInput, ProductPatch, ProductOutput, ProductPage, Pagination, ReserveInput
from product_api.services.products import active_product, create_product, commit_product, reserve_product

blp = Blueprint("products", __name__, url_prefix="/api/v1/products", description="Product CRUD and reservation")

@blp.route("")
class Products(MethodView):
    @blp.arguments(Pagination, location="query", unknown="raise")
    @blp.response(200, ProductPage)
    def get(self, query):
        total = db.session.scalar(select(func.count()).select_from(Product).where(Product.archived.is_(False)))
        items = db.session.scalars(select(Product).where(Product.archived.is_(False)).order_by(Product.id)
            .offset((query["page"] - 1) * query["size"]).limit(query["size"])).all()
        return dict(items=items, total=total, **query)

    @blp.arguments(ProductInput)
    @blp.response(201, ProductOutput)
    def post(self, data):
        return create_product(data)

@blp.route("/<int:product_id>")
class ProductDetail(MethodView):
    @blp.response(200, ProductOutput)
    def get(self, product_id):
        return active_product(product_id)

    @blp.arguments(ProductPatch)
    @blp.response(200, ProductOutput)
    def patch(self, data, product_id):
        product = active_product(product_id)
        for key, value in data.items():
            setattr(product, key, value)
        commit_product()
        return product

    @blp.response(204)
    def delete(self, product_id):
        product = active_product(product_id)
        product.archived = True
        commit_product()

@blp.route("/<int:product_id>/reserve")
class ProductReserve(MethodView):
    @blp.arguments(ReserveInput)
    @blp.response(200, ProductOutput)
    def post(self, data, product_id):
        return reserve_product(product_id, data["qty"])
