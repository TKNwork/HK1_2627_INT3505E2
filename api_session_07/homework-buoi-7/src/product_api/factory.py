from pathlib import Path
from flask import Flask, request
from flask_smorest import Api
from sqlalchemy import event
from werkzeug.exceptions import UnsupportedMediaType
from .config import settings
from .extensions import db, migrate
from .errors import ErrorSchema, register_errors
from .logging_config import configure_logging


def create_app(config=None):
    app = Flask(__name__, instance_path=str(Path("instance").resolve()))
    app.config.from_mapping(settings())
    if config:
        app.config.update(config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("postgresql"):
        app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {
            "pool_pre_ping": True, "pool_timeout": 5,
            "connect_args": {"connect_timeout": 3, "options": "-c statement_timeout=5000"}})
    db.init_app(app)
    from . import models
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            @event.listens_for(db.engine, "connect")
            def sqlite_foreign_keys(connection, record):
                connection.execute("PRAGMA foreign_keys=ON")
    migrate.init_app(app, db)
    configure_logging(app)
    api = Api()
    api.ERROR_SCHEMA = ErrorSchema
    api.init_app(app)
    from .api.products import blp as products
    from .api.orders import blp as orders
    from .api.health import blp as health
    for blueprint in (products, orders, health):
        api.register_blueprint(blueprint)
    # Code-first shared error contract, including business and media-type errors.
    for path in api.spec.to_dict()["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "responses" in operation:
                for code in (400, 404, 405, 409, 415, 422, 500, 503):
                    operation["responses"].setdefault(str(code), {
                        "description": "Error response", "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}}}})
    register_errors(app)

    @app.before_request
    def require_json():
        if request.method in ("POST", "PATCH") and request.blueprint in ("products", "orders"):
            if not request.is_json:
                raise UnsupportedMediaType("Content-Type must be application/json.")
            request.get_json()  # Malformed JSON => 400 before schema validation.
    return app
