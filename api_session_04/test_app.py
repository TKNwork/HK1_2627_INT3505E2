"""
test_app.py - Bộ kiểm thử tự động toàn diện cho api_session_04
Kiểm tra OpenAPI Spec, Swagger UI và các chức năng CRUD API
"""

import unittest
import json
from app import app, BOOKS


class TestBooksAPI(unittest.TestCase):
    def setUp(self):
        """Khởi tạo test client trước mỗi ca kiểm thử."""
        self.client = app.test_client()
        self.client.testing = True

    def test_01_openapi_json_endpoint(self):
        """Xác minh GET /openapi.json trả HTTP 200 và cấu trúc OpenAPI 3.0.3 hợp lệ."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("openapi"), "3.0.3")

        # Kiểm tra khối info
        self.assertIn("info", data)
        self.assertEqual(data["info"].get("title"), "Books Management API")
        self.assertEqual(data["info"].get("version"), "1.0.0")

        # Kiểm tra khối paths
        self.assertIn("paths", data)
        paths = data["paths"]
        self.assertIn("/books", paths)
        self.assertIn("get", paths["/books"])
        self.assertIn("post", paths["/books"])

        self.assertIn("/books/{bid}", paths)
        self.assertIn("get", paths["/books/{bid}"])
        self.assertIn("put", paths["/books/{bid}"])
        self.assertIn("patch", paths["/books/{bid}"])
        self.assertIn("delete", paths["/books/{bid}"])

        # Kiểm tra components schemas
        self.assertIn("components", data)
        self.assertIn("schemas", data["components"])
        schemas = data["components"]["schemas"]
        self.assertIn("Book", schemas)
        self.assertIn("BookCreateInput", schemas)
        self.assertIn("BookUpdateInput", schemas)
        self.assertIn("BookPatchInput", schemas)
        self.assertIn("BookListResponse", schemas)
        self.assertIn("ErrorResponse", schemas)

    def test_02_swagger_ui_endpoint(self):
        """Xác minh GET /docs trả HTTP 200 và giao diện HTML Swagger UI."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        html = response.data.decode("utf-8")
        self.assertIn("swagger-ui", html)
        self.assertIn("/openapi.json", html)
        self.assertIn("SwaggerUIBundle", html)

    def test_03_root_redirect(self):
        """Xác minh GET / chuyển hướng 302 sang /docs."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get("Location"), "/docs")

    def test_04_list_books_default(self):
        """Xác minh GET /books trả HTTP 200 kèm danh sách sách và metadata phân trang."""
        response = self.client.get("/books")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn("data", data)
        self.assertIn("pagination", data)
        self.assertIn("_links", data)

        self.assertIsInstance(data["data"], list)
        self.assertGreaterEqual(len(data["data"]), 1)
        self.assertEqual(data["pagination"]["page"], 1)
        self.assertEqual(response.headers.get("Cache-Control"), "public, max-age=30")

    def test_05_list_books_filter_author(self):
        """Xác minh lọc theo tác giả author=Robert C. Martin."""
        response = self.client.get("/books?author=Robert C. Martin")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for item in data["data"]:
            self.assertEqual(item["author"], "Robert C. Martin")

    def test_06_list_books_search_query(self):
        """Xác minh tìm kiếm từ khóa trong tiêu đề q=Clean."""
        response = self.client.get("/books?q=Clean")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for item in data["data"]:
            self.assertIn("clean", item["title"].lower())

    def test_07_list_books_invalid_pagination(self):
        """Xác minh GET /books với page không phải số trả về 400."""
        response = self.client.get("/books?page=not-a-number")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("error"), "bad request")

    def test_08_get_book_detail_success(self):
        """Xác minh GET /books/1 trả về đúng thông tin cuốn sách và cache header."""
        response = self.client.get("/books/1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("id"), 1)
        self.assertEqual(data.get("title"), "Clean Code")
        self.assertEqual(response.headers.get("Cache-Control"), "max-age=60")

    def test_09_get_book_detail_not_found(self):
        """Xác minh GET /books/9999 trả về 404."""
        response = self.client.get("/books/9999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data.get("error"), "not found")

    def test_10_create_book_success(self):
        """Xác minh POST /books tạo thành công trả về 201 kèm Location header."""
        payload = {
            "title": "Design Patterns",
            "author": "Gang of Four",
            "isbn": "9780201633610",
            "price": 54.99
        }
        response = self.client.post("/books", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "Design Patterns")
        self.assertEqual(data["author"], "Gang of Four")
        self.assertEqual(response.headers.get("Location"), f"/books/{data['id']}")

    def test_11_create_book_validation_error(self):
        """Xác minh POST /books thiếu trường bắt buộc trả về 400."""
        # Thiếu author
        response = self.client.post("/books", json={"title": "Missing Author"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("error"), "bad request")

    def test_12_create_book_unsupported_media_type(self):
        """Xác minh POST /books gửi dạng plain text trả về 415."""
        response = self.client.post("/books", data="plain text data", content_type="text/plain")
        self.assertEqual(response.status_code, 415)
        data = response.get_json()
        self.assertEqual(data.get("error"), "unsupported media type")

    def test_13_update_book_put_success(self):
        """Xác minh PUT /books/2 thay thế toàn bộ thành công trả về 200."""
        payload = {
            "title": "Refactoring (2nd Edition)",
            "author": "Martin Fowler",
            "isbn": "9780134757599",
            "price": 59.99
        }
        response = self.client.put("/books/2", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["title"], "Refactoring (2nd Edition)")
        self.assertEqual(data["price"], 59.99)

    def test_14_update_book_put_validation_fail(self):
        """Xác minh PUT /books/2 thiếu title hoặc author trả về 422."""
        payload = {"title": "Only Title"}
        response = self.client.put("/books/2", json=payload)
        self.assertEqual(response.status_code, 422)
        data = response.get_json()
        self.assertEqual(data.get("error"), "unprocessable entity")

    def test_15_update_book_put_not_found(self):
        """Xác minh PUT /books/9999 trả về 404."""
        payload = {"title": "Test", "author": "Test Author"}
        response = self.client.put("/books/9999", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_16_patch_book_success(self):
        """Xác minh PATCH /books/3 cập nhật một phần trường trả về 200."""
        payload = {"price": 42.5}
        response = self.client.patch("/books/3", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["price"], 42.5)
        self.assertEqual(data["title"], "Flask Web Development")

    def test_17_patch_book_negative_price(self):
        """Xác minh PATCH /books/3 với giá âm trả về 422."""
        payload = {"price": -10.0}
        response = self.client.patch("/books/3", json=payload)
        self.assertEqual(response.status_code, 422)
        data = response.get_json()
        self.assertEqual(data.get("error"), "unprocessable entity")

    def test_18_delete_book_success_and_not_found(self):
        """Xác minh DELETE /books/<id> xóa thành công trả về 204 và xóa lần nữa trả về 404."""
        # Tạo trước một cuốn sách để xóa
        res_create = self.client.post("/books", json={"title": "To Delete", "author": "Someone"})
        bid = res_create.get_json()["id"]

        # Xóa cuốn sách
        res_del = self.client.delete(f"/books/{bid}")
        self.assertEqual(res_del.status_code, 204)

        # Kiểm tra lấy lại phải trả 404
        res_get = self.client.get(f"/books/{bid}")
        self.assertEqual(res_get.status_code, 404)

        # Xóa lại lần nữa phải trả 404
        res_del_again = self.client.delete(f"/books/{bid}")
        self.assertEqual(res_del_again.status_code, 404)


if __name__ == "__main__":
    unittest.main()
