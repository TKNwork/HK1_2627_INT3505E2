from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from product_api.extensions import db

def test_health_no_database_queries(app, client):
    def fail(*args, **kwargs):
        raise AssertionError("Liveness must not access the database")
    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", fail)
        try:
            assert client.get("/healthz").json == {"status": "alive"}
        finally:
            event.remove(db.engine, "before_cursor_execute", fail)

def test_ready_success(client):
    assert client.get("/ready").status_code == 200

def test_ready_failure(app, client, monkeypatch):
    with app.app_context():
        def fail(*args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("private connection string"))
        monkeypatch.setattr(db.engine, "connect", fail)
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json["error"] == "not_ready"
    assert "private" not in response.text

def test_openapi(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json
    assert spec["openapi"] == "3.0.3"
    assert set(spec["paths"]["/api/v1/products"]) >= {"get", "post"}
    assert set(spec["paths"]["/api/v1/products/{product_id}"]) >= {"get", "patch", "delete"}
    for path in ("/healthz", "/ready", "/api/v1/orders", "/api/v1/orders/{order_id}", "/api/v1/products/{product_id}/reserve"):
        assert path in spec["paths"]
    assert spec["paths"]["/api/v1/products"]["post"]["responses"]["409"]["content"]["application/json"]["schema"]["$ref"]
    assert client.get("/docs").status_code == 200

def test_json_log(client, app):
    import json
    from io import StringIO
    stream = StringIO()
    handler = app.logger.handlers[0]
    old_stream = handler.setStream(stream)
    app.logger.setLevel("INFO")
    try:
        response = client.get("/healthz")
    finally:
        handler.setStream(old_stream)
    lines = stream.getvalue().splitlines()
    entry = json.loads(lines[-1])
    assert {"timestamp", "level", "message", "request_id", "method", "path", "status_code", "latency_ms"} <= entry.keys()
    assert entry["request_id"] == response.headers["X-Request-ID"]
