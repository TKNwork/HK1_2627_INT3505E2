"""
app.py - Ứng dụng Flask Books Management API tích hợp OpenAPI & Swagger UI
Môn học: Kiến trúc Hướng Dịch vụ (SOA) - Bài thực hành cá nhân Buổi 4
Tác giả: Sinh viên thực hành SOA
"""

from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, make_response, redirect, Response

from schemas import (
    BookSchema,
    BookCreateInputSchema,
    BookUpdateInputSchema,
    BookPatchInputSchema,
    PaginationMetaSchema,
    BookListResponseSchema,
    ErrorResponseSchema
)
from openapi import create_api_spec, get_swagger_ui_html

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Khởi tạo đặc tả OpenAPI 3.0.3 thông qua APISpec
spec = create_api_spec()

# Tham số phân trang mặc định và giới hạn
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Bộ nhớ giả lập lưu trữ danh sách sách (In-memory Storage) kế thừa từ Buổi 2
BOOKS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "price": 45.0
    },
    {
        "id": 2,
        "title": "Refactoring",
        "author": "Martin Fowler",
        "isbn": "9780201485677",
        "price": 55.0
    },
    {
        "id": 3,
        "title": "Flask Web Development",
        "author": "Miguel Grinberg",
        "isbn": "9781491991732",
        "price": 40.0
    },
    {
        "id": 4,
        "title": "Clean Architecture",
        "author": "Robert C. Martin",
        "isbn": "9780134494166",
        "price": 50.0
    }
]

_next_id: int = 5


def _find_book(bid: int) -> Optional[Dict[str, Any]]:
    """Tìm cuốn sách theo ID trong danh sách BOOKS."""
    return next((b for b in BOOKS if b["id"] == bid), None)


def _find_book_index(bid: int) -> Optional[int]:
    """Tìm vị trí index của cuốn sách theo ID."""
    return next((i for i, b in enumerate(BOOKS) if b["id"] == bid), None)


# ============================================================================
# ENDPOINTS TÀI LIỆU (SWAGGER UI & OPENAPI JSON)
# ============================================================================

@app.route("/", methods=["GET"])
def index():
    """Chuyển hướng trang chủ về Swagger UI (/docs)."""
    return redirect("/docs", code=302)


@app.route("/openapi.json", methods=["GET"])
def get_openapi_json():
    """Trả về đặc tả OpenAPI specification dạng JSON chuẩn 3.0.3."""
    return jsonify(spec.to_dict()), 200


@app.route("/docs", methods=["GET"])
def swagger_ui():
    """Giao diện Swagger UI tương tác trực tiếp với API."""
    html_content = get_swagger_ui_html(
        spec_url="/openapi.json",
        title="Books Management API - Swagger UI"
    )
    return Response(html_content, mimetype="text/html"), 200


# ============================================================================
# CÁC ENDPOINT QUẢN LÝ SÁCH (BOOKS API)
# ============================================================================

@app.route("/books", methods=["GET"])
def list_books():
    """Lấy danh sách sách có hỗ trợ phân trang, lọc theo tác giả và tìm kiếm theo tên.
    ---
    get:
      summary: Lấy danh sách sách
      description: Trả về danh sách sách có phân trang (page, size) và lọc theo tác giả (author) hoặc từ khóa tìm kiếm (q).
      tags:
        - Books
      parameters:
        - in: query
          name: page
          required: false
          schema:
            type: integer
            default: 1
            minimum: 1
          description: Trang hiện tại (bắt đầu từ 1)
        - in: query
          name: size
          required: false
          schema:
            type: integer
            default: 20
            minimum: 1
            maximum: 100
          description: Số lượng bản ghi trên một trang
        - in: query
          name: author
          required: false
          schema:
            type: string
          description: Lọc chính xác theo tên tác giả
        - in: query
          name: q
          required: false
          schema:
            type: string
          description: Tìm kiếm từ khóa xuất hiện trong tiêu đề sách
      responses:
        200:
          description: Lấy danh sách sách thành công
          headers:
            Cache-Control:
              description: Cấu hình bộ nhớ đệm phản hồi
              schema:
                type: string
                example: public, max-age=30
          content:
            application/json:
              schema: BookListResponseSchema
        400:
          description: Tham số phân trang page hoặc size không hợp lệ
          content:
            application/json:
              schema: ErrorResponseSchema
    """
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_PAGE_SIZE))
    except ValueError:
        return jsonify({
            "error": "bad request",
            "message": "Các tham số 'page' và 'size' phải là số nguyên hợp lệ."
        }), 400

    page = max(page, 1)
    size = max(min(size, MAX_PAGE_SIZE), 1)

    # 1. Lọc dữ liệu
    filtered = BOOKS[:]
    author_filter = request.args.get("author")
    if author_filter:
        author_clean = author_filter.strip().lower()
        filtered = [b for b in filtered if b.get("author", "").strip().lower() == author_clean]

    q_filter = (request.args.get("q") or "").strip().lower()
    if q_filter:
        filtered = [b for b in filtered if q_filter in b.get("title", "").strip().lower()]

    # 2. Phân trang
    total = len(filtered)
    start_index = (page - 1) * size
    end_index = start_index + size
    items = filtered[start_index:end_index]
    total_pages = (total + size - 1) // size if total > 0 else 1

    # 3. Tạo HATEOAS Links
    def build_page_link(target_page: int) -> str:
        url = f"/books?page={target_page}&size={size}"
        if author_filter:
            url += f"&author={author_filter}"
        if q_filter:
            url += f"&q={q_filter}"
        return url

    links = {
        "self": {"href": build_page_link(page)},
        "first": {"href": build_page_link(1)},
        "last": {"href": build_page_link(max(total_pages, 1))},
        "prev": {"href": build_page_link(page - 1)} if page > 1 else None,
        "next": {"href": build_page_link(page + 1)} if end_index < total else None
    }

    response_payload = {
        "data": items,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages
        },
        "_links": links
    }

    resp = make_response(jsonify(response_payload), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp


@app.route("/books", methods=["POST"])
def create_book():
    """Tạo mới một cuốn sách.
    ---
    post:
      summary: Thêm cuốn sách mới
      description: Tạo mới một bản ghi sách trong hệ thống. Trả về thông tin cuốn sách và header Location.
      tags:
        - Books
      requestBody:
        required: true
        description: Dữ liệu khởi tạo cuốn sách
        content:
          application/json:
            schema: BookCreateInputSchema
      responses:
        201:
          description: Tạo sách thành công
          headers:
            Location:
              description: URI dẫn tới tài nguyên sách vừa được tạo
              schema:
                type: string
                example: /books/5
          content:
            application/json:
              schema: BookSchema
        400:
          description: Thiếu dữ liệu bắt buộc (title hoặc author)
          content:
            application/json:
              schema: ErrorResponseSchema
        415:
          description: Yêu cầu định dạng Content-Type là application/json
          content:
            application/json:
              schema: ErrorResponseSchema
    """
    global _next_id

    if not request.is_json:
        return jsonify({
            "error": "unsupported media type",
            "message": "Content-Type yêu cầu phải là application/json."
        }), 415

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    author = body.get("author")

    if not title or not isinstance(title, str) or not title.strip():
        return jsonify({
            "error": "bad request",
            "message": "Trường 'title' là bắt buộc và không được để trống."
        }), 400

    if not author or not isinstance(author, str) or not author.strip():
        return jsonify({
            "error": "bad request",
            "message": "Trường 'author' là bắt buộc và không được để trống."
        }), 400

    new_book = {
        "id": _next_id,
        "title": title.strip(),
        "author": author.strip(),
        "isbn": body.get("isbn"),
        "price": float(body["price"]) if body.get("price") is not None else None
    }
    BOOKS.append(new_book)
    _next_id += 1

    resp = make_response(jsonify(new_book), 201)
    resp.headers["Location"] = f"/books/{new_book['id']}"
    return resp


@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid: int):
    """Lấy thông tin chi tiết một cuốn sách theo ID.
    ---
    get:
      summary: Lấy chi tiết sách theo ID
      description: Trả về thông tin đầy đủ của cuốn sách có mã định danh ID.
      tags:
        - Books
      parameters:
        - in: path
          name: bid
          required: true
          schema:
            type: integer
          description: Mã định danh ID của cuốn sách
      responses:
        200:
          description: Lấy thông tin sách thành công
          headers:
            Cache-Control:
              description: Header bộ nhớ đệm
              schema:
                type: string
                example: max-age=60
          content:
            application/json:
              schema: BookSchema
        404:
          description: Không tìm thấy cuốn sách với ID đã cho
          content:
            application/json:
              schema: ErrorResponseSchema
    """
    book = _find_book(bid)
    if not book:
        return jsonify({
            "error": "not found",
            "message": f"Không tìm thấy cuốn sách có ID={bid}."
        }), 404

    resp = make_response(jsonify(book), 200)
    resp.headers["Cache-Control"] = "max-age=60"
    return resp


@app.route("/books/<int:bid>", methods=["PUT"], endpoint="update_book")
def update_book(bid: int):
    """Thay thế toàn bộ thông tin một cuốn sách theo ID.
    ---
    put:
      summary: Thay thế toàn bộ thông tin sách (PUT)
      description: Cập nhật toàn bộ thuộc tính của cuốn sách. Các trường title và author là bắt buộc.
      tags:
        - Books
      parameters:
        - in: path
          name: bid
          required: true
          schema:
            type: integer
          description: Mã định danh ID của cuốn sách
      requestBody:
        required: true
        description: Dữ liệu toàn bộ của cuốn sách cần cập nhật
        content:
          application/json:
            schema: BookUpdateInputSchema
      responses:
        200:
          description: Cập nhật thông tin thành công
          content:
            application/json:
              schema: BookSchema
        404:
          description: Không tìm thấy cuốn sách với ID đã cho
          content:
            application/json:
              schema: ErrorResponseSchema
        422:
          description: Dữ liệu gửi lên thiếu trường bắt buộc (title hoặc author)
          content:
            application/json:
              schema: ErrorResponseSchema
    """
    index = _find_book_index(bid)
    if index is None:
        return jsonify({
            "error": "not found",
            "message": f"Không tìm thấy cuốn sách có ID={bid} để cập nhật."
        }), 404

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    author = body.get("author")

    if not title or not str(title).strip() or not author or not str(author).strip():
        return jsonify({
            "error": "unprocessable entity",
            "message": "Yêu cầu bắt buộc phải có đầy đủ 'title' và 'author'."
        }), 422

    price = body.get("price")
    if price is not None and float(price) < 0:
        return jsonify({
            "error": "unprocessable entity",
            "message": "Giá sách ('price') phải lớn hơn hoặc bằng 0."
        }), 422

    BOOKS[index] = {
        "id": bid,
        "title": str(title).strip(),
        "author": str(author).strip(),
        "isbn": body.get("isbn"),
        "price": float(price) if price is not None else None
    }
    return jsonify(BOOKS[index]), 200


@app.route("/books/<int:bid>", methods=["PATCH"], endpoint="patch_book")
def patch_book(bid: int):
    """Cập nhật một phần thông tin cuốn sách theo ID.
    ---
    patch:
      summary: Cập nhật một phần thông tin sách (PATCH)
      description: Chỉ cập nhật các trường được truyền trong request (title, author, isbn, price).
      tags:
        - Books
      parameters:
        - in: path
          name: bid
          required: true
          schema:
            type: integer
          description: Mã định danh ID của cuốn sách
      requestBody:
        required: true
        description: Các trường cần cập nhật
        content:
          application/json:
            schema: BookPatchInputSchema
      responses:
        200:
          description: Cập nhật thành công
          content:
            application/json:
              schema: BookSchema
        404:
          description: Không tìm thấy cuốn sách với ID đã cho
          content:
            application/json:
              schema: ErrorResponseSchema
        422:
          description: Dữ liệu không hợp lệ (ví dụ price âm)
          content:
            application/json:
              schema: ErrorResponseSchema
    """
    index = _find_book_index(bid)
    if index is None:
        return jsonify({
            "error": "not found",
            "message": f"Không tìm thấy cuốn sách có ID={bid} để cập nhật."
        }), 404

    body = request.get_json(silent=True) or {}

    if "price" in body and body["price"] is not None:
        try:
            val = float(body["price"])
            if val < 0:
                return jsonify({
                    "error": "unprocessable entity",
                    "message": "Giá sách ('price') phải lớn hơn hoặc bằng 0."
                }), 422
            BOOKS[index]["price"] = val
        except (ValueError, TypeError):
            return jsonify({
                "error": "unprocessable entity",
                "message": "Giá sách ('price') phải là số hợp lệ."
            }), 422

    if "title" in body:
        t = body["title"]
        if t is not None and str(t).strip():
            BOOKS[index]["title"] = str(t).strip()

    if "author" in body:
        a = body["author"]
        if a is not None and str(a).strip():
            BOOKS[index]["author"] = str(a).strip()

    if "isbn" in body:
        BOOKS[index]["isbn"] = body["isbn"]

    return jsonify(BOOKS[index]), 200


@app.route("/books/<int:bid>", methods=["DELETE"], endpoint="delete_book")
def delete_book(bid: int):
    """Xóa một cuốn sách khỏi hệ thống theo ID.
    ---
    delete:
      summary: Xóa cuốn sách theo ID (DELETE)
      description: Xóa cuốn sách tương ứng với mã định danh ID. Trả về mã HTTP 204 No Content nếu xóa thành công.
      tags:
        - Books
      parameters:
        - in: path
          name: bid
          required: true
          schema:
            type: integer
          description: Mã định danh ID của cuốn sách cần xóa
      responses:
        204:
          description: Xóa cuốn sách thành công (Không có body trả về)
        404:
          description: Không tìm thấy cuốn sách với ID đã cho
          content:
            application/json:
              schema: ErrorResponseSchema
    """
    index = _find_book_index(bid)
    if index is None:
        return jsonify({
            "error": "not found",
            "message": f"Không tìm thấy cuốn sách có ID={bid} để xóa."
        }), 404

    BOOKS.pop(index)
    return "", 204


# ============================================================================
# ĐĂNG KÝ CÁC PATH VÀO APISPEC
# ============================================================================

with app.test_request_context():
    spec.path(view=list_books)
    spec.path(view=create_book)
    spec.path(view=get_book)
    spec.path(view=update_book)
    spec.path(view=patch_book)
    spec.path(view=delete_book)


# ============================================================================
# ENTRY POINT KHỞI CHẠY ỨNG DỤNG
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Khởi chạy Books Management API (SOA Buổi 4)")
    print("📖 OpenAPI Specification: http://localhost:5000/openapi.json")
    print("🌐 Swagger UI Documentation: http://localhost:5000/docs")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
