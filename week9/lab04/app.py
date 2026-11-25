from flask import Flask, jsonify, request

from .gateway import dispatch


app = Flask(__name__)
app.config["V2_PERCENT"] = 5
app.config.from_prefixed_env(prefix="LAB04")

if type(app.config["V2_PERCENT"]) is not int or not 0 <= app.config["V2_PERCENT"] <= 100:
    raise ValueError("LAB04_V2_PERCENT must be an integer from 0 to 100")


@app.post("/orders")
def create_order():
    body = request.get_json()
    if not isinstance(body, dict):
        return jsonify(error="expected a JSON object"), 400

    account_id = body.get("account_id")
    if not isinstance(account_id, str) or not account_id.strip():
        return jsonify(error="account_id must be a non-empty string"), 400

    cohort = request.headers.get("X-Cohort", "")
    version, result, status = dispatch(body, cohort, app.config["V2_PERCENT"])
    response = jsonify(result)
    response.headers["X-Order-Handler"] = version
    return response, status
