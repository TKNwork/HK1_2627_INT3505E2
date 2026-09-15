# app4.py — Bài 4: Route Parameters & Query Parameters
# pyrefly: ignore [missing-import]
from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS = [
    {"id": "1", "title": "Python Programming", "t": "Python Programming"},
    {"id": "2", "title": "Flask Web Development", "t": "Flask Web Development"},
    {"id": "3", "title": "SOA & Microservices", "t": "SOA & Microservices"},
]

def find_by_id(book_id):
    return next((b for b in BOOKS if b["id"] == str(book_id)), None)

# /books/<id> — id là string
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# Ép kiểu int ngay từ URL
@app.route("/items/<int:item_id>")
def get_item(item_id):  # int sẵn
    return jsonify({"id": item_id}), 200

# /books?limit=10&offset=0&q=python
@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    q = request.args.get("q", "").strip().lower()

    items = [b for b in BOOKS if q in b["t"].lower()]
    paged_items = items[offset:offset + limit]
    return jsonify({"items": paged_items}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
