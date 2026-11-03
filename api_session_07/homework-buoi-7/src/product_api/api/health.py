from flask_smorest import Blueprint
from marshmallow import Schema, fields
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from product_api.extensions import db

blp = Blueprint("health", __name__, description="Liveness and database readiness")

class HealthOutput(Schema):
    status = fields.String()

@blp.route("/healthz")
@blp.response(200, HealthOutput)
def healthz():
    return {"status": "alive"}

@blp.route("/ready")
@blp.response(200, HealthOutput)
def ready():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        from product_api.errors import ApiError
        raise ApiError(503, "not_ready", "Database unavailable.")
    return {"status": "ready"}
