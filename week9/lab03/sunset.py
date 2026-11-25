import logging
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import wraps

from flask import jsonify, make_response, request


log = logging.getLogger("sunset")


def deprecate_at(sunset_date, replacement=None):
    sunset = format_datetime(sunset_date.astimezone(timezone.utc), usegmt=True)

    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if datetime.now(timezone.utc) >= sunset_date:
                return jsonify(error="gone", sunset=sunset, use_instead=replacement), 410

            response = make_response(view(*args, **kwargs))
            response.headers["Sunset"] = sunset
            response.headers["Deprecation"] = "true"
            if replacement:
                response.headers["Link"] = f'<{replacement}>; rel="successor-version"'
            log.warning("deprecated_call %s %s", request.path, request.remote_addr)
            return response

        return wrapped

    return decorate
