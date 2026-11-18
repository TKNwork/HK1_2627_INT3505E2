from flask import Blueprint

from .users_data import get_user


bp = Blueprint("v1", __name__, url_prefix="/users")


@bp.get("/<int:uid>")
def get(uid):
    user = get_user(uid)
    if user is None:
        return {"error": "nf"}, 404

    return {
        "id": uid,
        "full_name": f"{user['first_name']} {user['last_name']}",
        "email": user["email"],
    }
