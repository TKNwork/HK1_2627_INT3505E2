import base64
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample Orders Data
ORDERS = [
    {"id": 1, "customer_id": 101, "status": "paid", "total": 150.0, "created_at": "2026-10-01T10:00:00Z"},
    {"id": 2, "customer_id": 102, "status": "pending", "total": 85.5, "created_at": "2026-10-01T11:30:00Z"},
    {"id": 3, "customer_id": 101, "status": "paid", "total": 200.0, "created_at": "2026-10-02T09:15:00Z"},
    {"id": 4, "customer_id": 103, "status": "shipped", "total": 45.0, "created_at": "2026-10-02T14:20:00Z"},
    {"id": 5, "customer_id": 102, "status": "paid", "total": 310.0, "created_at": "2026-10-03T08:00:00Z"},
    {"id": 6, "customer_id": 104, "status": "cancelled", "total": 60.0, "created_at": "2026-10-03T16:45:00Z"},
    {"id": 7, "customer_id": 101, "status": "paid", "total": 99.9, "created_at": "2026-10-04T12:00:00Z"},
    {"id": 8, "customer_id": 103, "status": "pending", "total": 175.25, "created_at": "2026-10-04T15:30:00Z"},
    {"id": 9, "customer_id": 105, "status": "paid", "total": 500.0, "created_at": "2026-10-05T09:00:00Z"},
    {"id": 10, "customer_id": 102, "status": "shipped", "total": 120.0, "created_at": "2026-10-05T11:10:00Z"},
    {"id": 11, "customer_id": 101, "status": "pending", "total": 65.0, "created_at": "2026-10-06T08:00:00Z"},
    {"id": 12, "customer_id": 104, "status": "paid", "total": 240.0, "created_at": "2026-10-06T14:00:00Z"},
]


def encode_cursor(last_id):
    """Mã hóa ID phần tử cuối thành chuỗi Cursor Base64."""
    payload = json.dumps({"id": last_id}).encode("utf-8")
    return base64.b64encode(payload).decode("utf-8")


def decode_cursor(cursor_str):
    """Giải mã chuỗi Cursor Base64. Trả về cursor_id hoặc ném Exception nếu hỏng."""
    try:
        decoded_bytes = base64.b64decode(cursor_str.encode("utf-8"), validate=True)
        data = json.loads(decoded_bytes.decode("utf-8"))
        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Missing id field in cursor payload")
        return int(data["id"])
    except Exception as e:
        raise ValueError(f"Invalid cursor format: {str(e)}")


@app.get("/orders")
def get_orders():
    # ─── (1) Parse Cursor ───
    cursor_param = request.args.get("cursor")
    cursor_id = None
    if cursor_param:
        try:
            cursor_id = decode_cursor(cursor_param)
        except ValueError as err:
            # Trả về HTTP 400 nếu cursor bị hỏng
            return jsonify({
                "error": "Bad Request",
                "message": str(err),
                "detail": f"Provided cursor '{cursor_param}' is invalid or corrupted."
            }), 400

    # Parse limit
    try:
        limit = int(request.args.get("limit", 10))
        if limit <= 0:
            limit = 10
    except ValueError:
        return jsonify({"error": "Bad Request", "message": "limit must be an integer"}), 400

    # ─── (2) Filter: status, customer_id ───
    filtered_orders = ORDERS[:]
    
    status_filter = request.args.get("status")
    if status_filter:
        filtered_orders = [
            o for o in filtered_orders 
            if o.get("status", "").lower() == status_filter.strip().lower()
        ]

    customer_id_filter = request.args.get("customer_id")
    if customer_id_filter:
        filtered_orders = [
            o for o in filtered_orders 
            if str(o.get("customer_id")) == customer_id_filter.strip()
        ]

    # ─── (3) Sort ───
    sort_param = request.args.get("sort", "id")
    reverse = sort_param.startswith("-")
    sort_field = sort_param.lstrip("-")
    
    valid_sort_fields = ["id", "customer_id", "status", "total", "created_at"]
    if sort_field not in valid_sort_fields:
        sort_field = "id"

    filtered_orders = sorted(filtered_orders, key=lambda x: x.get(sort_field), reverse=reverse)

    # ─── Áp dụng Cursor Pagination ───
    if cursor_id is not None:
        # Tìm vị trí bản ghi khớp với cursor_id
        start_index = -1
        for idx, item in enumerate(filtered_orders):
            if item["id"] == cursor_id:
                start_index = idx
                break
        
        if start_index != -1:
            filtered_orders = filtered_orders[start_index + 1:]
        else:
            # Nếu cursor_id không thuộc tập filter hiện tại, lọc id > cursor_id
            filtered_orders = [o for o in filtered_orders if o["id"] > cursor_id]

    # Lấy số phần tử theo limit
    page_items = filtered_orders[:limit]
    has_more = len(filtered_orders) > limit
    next_cursor = encode_cursor(page_items[-1]["id"]) if (has_more and page_items) else None

    # ─── (4) Sparse Fieldsets ───
    fields_param = request.args.get("fields")
    if fields_param:
        requested_fields = [f.strip() for f in fields_param.split(",") if f.strip()]
        sparse_items = []
        for item in page_items:
            sparse_item = {k: v for k, v in item.items() if k in requested_fields}
            sparse_items.append(sparse_item)
        final_items = sparse_items
    else:
        final_items = page_items

    # Trả về kết quả JSON
    return jsonify({
        "data": final_items,
        "pagination": {
            "limit": limit,
            "has_more": has_more,
            "next_cursor": next_cursor
        }
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
