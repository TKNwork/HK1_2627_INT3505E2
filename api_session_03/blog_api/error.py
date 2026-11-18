from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class ProblemError(Exception):
    def __init__(
        self,
        status,
        title,
        detail,
        type_url="about:blank"
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_url = type_url
        super().__init__(detail)


def register_error_handlers(app):

    # Lỗi do mình chủ động raise
    @app.errorhandler(ProblemError)
    def handle_problem_error(error):

        body = {
            "type": error.type_url,
            "title": error.title,
            "detail": error.detail,
            "status": error.status,
            "instance": request.path
        }

        response = jsonify(body)
        response.status_code = error.status
        response.headers["Content-Type"] = "application/problem+json"

        return response


    # Các lỗi HTTP của Flask: 404, 405,...
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):

        body = {
            "type": "about:blank",
            "title": error.name,
            "detail": error.description,
            "status": error.code,
            "instance": request.path
        }

        response = jsonify(body)
        response.status_code = error.code
        response.headers["Content-Type"] = "application/problem+json"

        return response


    # Exception chưa được bắt -> 500
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):

        # Log chi tiết ở phía server
        app.logger.exception(error)

        body = {
            "type": "about:blank",
            "title": "Internal Server Error",
            "detail": "An unexpected error occurred.",
            "status": 500,
            "instance": request.path
        }

        response = jsonify(body)
        response.status_code = 500
        response.headers["Content-Type"] = "application/problem+json"

        return response