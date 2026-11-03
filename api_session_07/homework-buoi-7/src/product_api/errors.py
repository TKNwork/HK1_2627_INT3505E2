from flask import g, jsonify, current_app, request
from marshmallow import Schema, fields as ma_fields
from werkzeug.exceptions import HTTPException
from product_api.extensions import db

class ErrorSchema(Schema):
    error = ma_fields.String()
    detail = ma_fields.String()
    fields = ma_fields.Dict()
    request_id = ma_fields.String()

class ApiError(Exception):
    def __init__(self, status, code, detail):
        self.status, self.code, self.detail = status, code, detail

def register_errors(app):
    @app.errorhandler(ApiError)
    def business_error(exc):
        db.session.rollback()
        return jsonify(error=exc.code, detail=exc.detail, request_id=g.request_id), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        codes = {400: "bad_request", 404: "not_found", 405: "method_not_allowed",
                 409: "conflict", 415: "unsupported_media_type", 422: "validation_error", 503: "not_ready"}
        body = dict(error=codes.get(exc.code, "http_error"), detail=exc.description, request_id=g.request_id)
        if hasattr(exc, "data") and "messages" in exc.data:
            body["fields"] = exc.data["messages"]
        response = jsonify(body)
        # Preserve protocol headers such as Allow for 405.
        for key, value in exc.get_headers():
            if key.lower() not in ("content-type", "content-length"):
                response.headers[key] = value
        return response, exc.code

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        db.session.rollback()
        import traceback
        frames = [{"file": frame.filename, "line": frame.lineno, "function": frame.name}
                  for frame in traceback.extract_tb(exc.__traceback__)]
        current_app.logger.error("unhandled_exception", extra={
            "exception_type": type(exc).__name__, "traceback_frames": frames,
            "request_id": g.request_id, "method": request.method,
            "path": request.path})
        return jsonify(error="internal_error", detail="Internal server error.", request_id=g.request_id), 500
