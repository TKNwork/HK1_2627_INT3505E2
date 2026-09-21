# app3.py — GET /books nâng cấp với Pagination + Filter + HATEOAS
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Tham số phân trang
DEFAULT_SIZE, MAX_SIZE = 20, 100

# Data mẫu giả lập
BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "R. Martin", "isbn": "9780132350884", "price": 45.0},
    {"id": 2, "title": "Refactoring", "author": "M. Fowler", "isbn": "9780201485677", "price": 55.0},
    {"id": 3, "title": "Flask Web Development", "author": "M. Grinberg", "isbn": "9781491991732", "price": 40.0},
    {"id": 4, "title": "Clean Architecture", "author": "R. Martin", "isbn": "9780134494166", "price": 50.0},
]
_next_id = 5

# ─── GET /books ─── List + Filter + Paginate + HATEOAS Links
@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify({"error": "page and size must be int"}), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    # Filter: author chính xác, q tìm trong title
    flt = BOOKS
    a = request.args.get("author")
    if a:
        flt = [b for b in flt if b.get("author", "").lower() == a.lower()]

    q = (request.args.get("q") or "").lower()
    if q:
        flt = [b for b in flt if q in b.get("title", "").lower()]

    # Paginate
    total = len(flt)
    start = (page - 1) * size
    end = start + size
    items = flt[start:end]
    last = (total + size - 1) // size if total > 0 else 1

    # HATEOAS links
    def u(p):
        query_extra = f"&author={a}" if a else ""
        query_extra += f"&q={q}" if q else ""
        return f"/books?page={p}&size={size}{query_extra}"

    links = {
        "self": {"href": u(page)},
        "first": {"href": u(1)},
        "last": {"href": u(max(last, 1))}
    }
    if page > 1:
        links["prev"] = {"href": u(page - 1)}
    if end < total:
        links["next"] = {"href": u(page + 1)}

    body = {
        "data": items,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": last
        },
        "_links": links
    }
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp

# ─── POST /books ─── Tạo mới sách
@app.post("/books")
def create_book():
    global _next_id
    if not request.is_json:
        return jsonify({"error": "expected JSON"}), 415

    p = request.get_json(silent=True) or {}
    t = p.get("title")
    a = p.get("author")

    if not t or not a:
        return jsonify({"error": "title and author required"}), 400

    book = {
        "id": _next_id,
        "title": t,
        "author": a,
        "isbn": p.get("isbn"),
        "price": p.get("price")
    }
    BOOKS.append(book)
    _next_id += 1

    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp

# ─── GET /books/<id> ─── Cache 60s
@app.get("/books/<int:bid>")
def fetch(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404
    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers["Cache-Control"] = "max-age=60"
    return resp

# ─── PUT /books/<id> ─── Thay thế toàn bộ
@app.put("/books/<int:bid>")
def put(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404
    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify({"error": "need title+author"}), 422
    BOOKS[i] = {
        "id": bid,
        "title": t.strip(),
        "author": a.strip(),
        "isbn": p.get("isbn"),
        "price": p.get("price")
    }
    return jsonify(BOOKS[i]), 200

# ─── PATCH /books/<id> ─── Cập nhật một phần
@app.patch("/books/<int:bid>")
def patch(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404
    p = request.get_json(silent=True) or {}
    if p.get("price") is not None and p.get("price", 0) < 0:
        return jsonify({"error": "price must be positive"}), 422
    for k in "title author isbn price".split():
        if k in p:
            BOOKS[i][k] = p[k]
    return jsonify(BOOKS[i]), 200

# ─── DELETE /books/<id> ─── Xóa sách
@app.delete("/books/<int:bid>")
def delete(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404
    BOOKS.pop(i)
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)