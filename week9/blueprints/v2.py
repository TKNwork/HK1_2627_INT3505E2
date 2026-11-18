from flask import Blueprint

from .users_data import get_user


bp = Blueprint("v2", __name__, url_prefix="/users")


@bp.get("/<int:uid>")
def get(uid):
    user = get_user(uid)
    if user is None:
        return {"error": "nf"}, 404

    return {
        "id": uid,
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
    }
