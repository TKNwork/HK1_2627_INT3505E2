from flask import Flask, jsonify

app = Flask(__name__)

ORDERS = {
    "1": {"id": "1", "status": "pending"},
    "2": {"id": "2", "status": "shipped"},
}

# GET /orders
@app.route("/orders", methods=["GET"])
def list_orders():
    return jsonify(list(ORDERS.values())), 200

# DELETE /orders/<order_id>
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)
    # 404 không tìm thấy
    if order is None:
        return jsonify({"error": "not found"}), 404
    # 409 lỗi nghiệp vụ 
    if order["status"] in ("shipped", "delivered"):
        return jsonify({"error": "cannot delete"}), 409

    ORDERS.pop(order_id, None)
    # 204 thành công
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
