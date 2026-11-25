from datetime import datetime, timezone

from flask import Flask

from blueprints.v1 import get as get_v1_user
from blueprints.v2 import bp as v2_bp
from .sunset import deprecate_at


V1_SUNSET = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
V2_USERS_PATH = "/api/v2/users"

app = Flask(__name__)
app.register_blueprint(v2_bp, url_prefix=V2_USERS_PATH)


@app.get("/api/v1/users/<int:uid>")
@deprecate_at(V1_SUNSET, replacement=V2_USERS_PATH)
def get_v1(uid):
    return get_v1_user(uid)
