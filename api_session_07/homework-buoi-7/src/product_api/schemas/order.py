from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from .product import JsonInteger, MAX_INT, ProductOutput

class OrderItemInput(Schema):
    product_id = JsonInteger(required=True, validate=validate.Range(min=1, max=MAX_INT))
    quantity = JsonInteger(required=True, validate=validate.Range(min=1, max=MAX_INT))

class OrderInput(Schema):
    items = fields.List(fields.Nested(OrderItemInput), required=True, validate=validate.Length(min=1, max=100))

    @validates_schema
    def unique_products(self, data, **kwargs):
        ids = [item["product_id"] for item in data["items"]]
        if len(ids) != len(set(ids)):
            raise ValidationError("Duplicate product_id is not allowed.", field_name="items")

class OrderItemOutput(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    quantity = fields.Integer()
    unit_price_cents = fields.Integer()
    product = fields.Nested(ProductOutput)

class OrderOutput(Schema):
    id = fields.Integer()
    created_at = fields.DateTime()
    items = fields.List(fields.Nested(OrderItemOutput))
    total_cents = fields.Integer()

class OrderPage(Schema):
    items = fields.List(fields.Nested(OrderOutput))
    page = fields.Integer()
    size = fields.Integer()
    total = fields.Integer()
