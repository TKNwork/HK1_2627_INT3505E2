import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from flask import g, request

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(),
                   "level": record.levelname, "message": record.getMessage()}
        for key in ("request_id", "method", "path", "status_code", "latency_ms", "exception_type", "traceback_frames"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)

def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app.logger.handlers = [handler]
    app.logger.propagate = False
    app.logger.setLevel(app.config["LOG_LEVEL"])

    @app.before_request
    def start_request():
        g.request_id = uuid.uuid4().hex
        g.start = time.perf_counter()

    @app.after_request
    def finish_request(response):
        response.headers["X-Request-ID"] = g.request_id
        app.logger.info("request_completed", extra={"request_id": g.request_id,
            "method": request.method, "path": request.path, "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - g.start) * 1000, 3)})
        return response
