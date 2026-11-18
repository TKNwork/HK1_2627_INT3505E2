import hashlib
import json
import sqlite3
from flask import Flask, request, jsonify, make_response, g

app = Flask(__name__)
DB_NAME = "database.db"
DEFAULT_SIZE, MAX_SIZE = 20, 100


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Khởi tạo database và dữ liệu ban đầu nếu chưa tồn tại."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT,
                price REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO books (title, author, isbn, price)
                VALUES (?, ?, ?, ?)
            """, [
                ("Clean Code", "R. Martin", "9780132350884", 45.0),
                ("Refactoring", "M. Fowler", "9780201485677", 55.0),
                ("Flask Web Development", "M. Grinberg", "9781491991732", 40.0),
                ("Clean Architecture", "R. Martin", "9780134494166", 50.0),
            ])
        cursor.execute("SELECT COUNT(*) FROM orders")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO orders (id, status)
                VALUES (?, ?)
            """, [
                ("1", "pending"),
                ("2", "shipped"),
            ])
        conn.commit()


def calculate_etag(data_dict):
    json_bytes = json.dumps(data_dict, sort_keys=True).encode("utf-8")
    hash_str = hashlib.sha256(json_bytes).hexdigest()[:16]
    return f'"{hash_str}"'


# ─── GET /books ─── 
@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify({"error": "page and size must be int"}), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    a = request.args.get("author")
    q = (request.args.get("q") or "").strip()

    db = get_db()
    conditions, params = [], []

    if a:
        conditions.append("LOWER(author) = LOWER(?)")
        params.append(a)
    if q:
        conditions.append("LOWER(title) LIKE LOWER(?)")
        params.append(f"%{q}%")

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    count_sql = f"SELECT COUNT(*) FROM books{where_clause}"
    cursor = db.execute(count_sql, params)
    total = cursor.fetchone()[0]

    start = (page - 1) * size
    select_sql = f"SELECT * FROM books{where_clause} LIMIT ? OFFSET ?"
    cursor = db.execute(select_sql, params + [size, start])
    items = [dict(row) for row in cursor.fetchall()]

    last = (total + size - 1) // size if total > 0 else 1

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
    if start + size < total:
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
    if not request.is_json:
        return jsonify({"error": "expected JSON"}), 415

    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")

    if not t or not a:
        return jsonify({"error": "title and author required"}), 400

    db = get_db()
    cursor = db.execute("""
        INSERT INTO books (title, author, isbn, price)
        VALUES (?, ?, ?, ?)
    """, (t.strip(), a.strip(), p.get("isbn"), p.get("price")))
    db.commit()

    bid = cursor.lastrowid
    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    book = dict(cursor.fetchone())

    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp


# ─── GET /books/<id> ───
@app.get("/books/<int:bid>")
def fetch_book(bid):
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    row = cursor.fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404

    book_dict = dict(row)
    etag = calculate_etag(book_dict)

    # Kiểm tra header If-None-Match từ client gửi lên
    client_etag = request.headers.get("If-None-Match")
    if client_etag:
        client_etag_clean = client_etag.strip()
        # So sánh match nguyên bản hoặc bỏ ngoặc kép
        if client_etag_clean == etag or client_etag_clean == etag.strip('"'):
            resp = make_response("", 304)
            resp.headers["ETag"] = etag
            return resp

    resp = make_response(jsonify(book_dict), 200)
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ─── PUT /books/<id> ─── 
@app.put("/books/<int:bid>")
def put_book(bid):
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    if cursor.fetchone() is None:
        return jsonify({"error": "not found"}), 404

    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify({"error": "need title+author"}), 422

    db.execute("""
        UPDATE books
        SET title = ?, author = ?, isbn = ?, price = ?
        WHERE id = ?
    """, (t.strip(), a.strip(), p.get("isbn"), p.get("price"), bid))
    db.commit()

    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    return jsonify(dict(cursor.fetchone())), 200


# ─── PATCH /books/<id> ───
@app.patch("/books/<int:bid>")
def patch_book(bid):
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    row = cursor.fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404

    p = request.get_json(silent=True) or {}
    if p.get("price") is not None and p.get("price", 0) < 0:
        return jsonify({"error": "price must be positive"}), 422

    updates, params = [], []
    for k in ["title", "author", "isbn", "price"]:
        if k in p:
            updates.append(f"{k} = ?")
            params.append(p[k])

    if updates:
        params.append(bid)
        sql = f"UPDATE books SET {', '.join(updates)} WHERE id = ?"
        db.execute(sql, params)
        db.commit()

    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    return jsonify(dict(cursor.fetchone())), 200


# ─── DELETE /books/<id> ─── 
@app.delete("/books/<int:bid>")
def delete_book(bid):
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE id = ?", (bid,))
    if cursor.fetchone() is None:
        return jsonify({"error": "not found"}), 404

    db.execute("DELETE FROM books WHERE id = ?", (bid,))
    db.commit()
    return "", 204


# ─── ORDERS ENDPOINTS ───
@app.get("/orders")
def list_orders():
    db = get_db()
    cursor = db.execute("SELECT * FROM orders")
    orders = [dict(row) for row in cursor.fetchall()]
    return jsonify(orders), 200


@app.get("/orders/<oid>")
def get_order(oid):
    db = get_db()
    cursor = db.execute("SELECT * FROM orders WHERE id = ?", (oid,))
    row = cursor.fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row)), 200


@app.post("/orders")
def create_order():
    if not request.is_json:
        return jsonify({"error": "expected JSON"}), 415

    p = request.get_json(silent=True) or {}
    oid = p.get("id")
    status = p.get("status", "pending")

    if not oid:
        return jsonify({"error": "order id required"}), 400

    db = get_db()
    cursor = db.execute("SELECT * FROM orders WHERE id = ?", (oid,))
    if cursor.fetchone() is not None:
        return jsonify({"error": "order already exists"}), 409

    db.execute("INSERT INTO orders (id, status) VALUES (?, ?)", (oid, status))
    db.commit()

    cursor = db.execute("SELECT * FROM orders WHERE id = ?", (oid,))
    order = dict(cursor.fetchone())
    resp = make_response(jsonify(order), 201)
    resp.headers["Location"] = f"/orders/{oid}"
    return resp


@app.delete("/orders/<oid>")
def delete_order(oid):
    db = get_db()
    cursor = db.execute("SELECT * FROM orders WHERE id = ?", (oid,))
    row = cursor.fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404

    order = dict(row)
    if order["status"] in ("shipped", "delivered"):
        return jsonify({"error": "cannot delete"}), 409

    db.execute("DELETE FROM orders WHERE id = ?", (oid,))
    db.commit()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
