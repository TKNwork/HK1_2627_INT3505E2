from marshmallow import Schema, fields, validate, validates_schema, ValidationError, pre_load, missing

MAX_INT = 2147483647

class JsonInteger(fields.Integer):
    def _deserialize(self, value, attr, data, **kwargs):
        if type(value) is not int:
            raise ValidationError("Must be a JSON integer (not boolean, string or float).")
        return super()._deserialize(value, attr, data, **kwargs)

class ProductInput(Schema):
    sku = fields.String(required=True, validate=[validate.Length(min=3, max=32), validate.Regexp(r"^[A-Z0-9][A-Z0-9_-]*$")])
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=4000))
    price_cents = JsonInteger(required=True, validate=validate.Range(min=0, max=MAX_INT))
    qty_in_stock = JsonInteger(load_default=0, validate=validate.Range(min=0, max=MAX_INT))

    @pre_load
    def normalize(self, data, **kwargs):
        if isinstance(data, dict):
            data = dict(data)
            for key in ("sku", "name"):
                if isinstance(data.get(key), str):
                    data[key] = data[key].strip()
            if isinstance(data.get("sku"), str):
                data["sku"] = data["sku"].upper()
        return data

class ProductPatch(ProductInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            field.load_default = missing

    @validates_schema
    def nonempty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one editable field is required.")

class ProductOutput(Schema):
    id = fields.Integer()
    sku = fields.String()
    name = fields.String()
    description = fields.String(allow_none=True)
    price_cents = fields.Integer()
    qty_in_stock = fields.Integer()
    archived = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class ReserveInput(Schema):
    qty = JsonInteger(required=True, validate=validate.Range(min=1, max=MAX_INT))

class Pagination(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=MAX_INT))
    size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))

class ProductPage(Schema):
    items = fields.List(fields.Nested(ProductOutput))
    page = fields.Integer()
    size = fields.Integer()
    total = fields.Integer()
