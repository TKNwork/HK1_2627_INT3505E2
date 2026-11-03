from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import select, func
from product_api.extensions import db
from product_api.models import Order
from product_api.schemas.product import Pagination
from product_api.schemas.order import OrderInput, OrderOutput, OrderPage
from product_api.services.orders import order_query, create_order, get_order

blp = Blueprint("orders", __name__, url_prefix="/api/v1/orders", description="Orders with nested items and current products")

@blp.route("")
class Orders(MethodView):
    @blp.arguments(Pagination, location="query", unknown="raise")
    @blp.response(200, OrderPage)
    def get(self, query):
        total = db.session.scalar(select(func.count()).select_from(Order))
        items = db.session.scalars(order_query().order_by(Order.id)
            .offset((query["page"] - 1) * query["size"]).limit(query["size"])).all()
        return dict(items=items, total=total, **query)

    @blp.arguments(OrderInput)
    @blp.response(201, OrderOutput)
    def post(self, data):
        return create_order(data)

@blp.route("/<int:order_id>")
class OrderDetail(MethodView):
    @blp.response(200, OrderOutput)
    def get(self, order_id):
        return get_order(order_id)
