# HƯỚNG DẪN CHỤP ẢNH MINH CHỨNG - BUỔI 4 (SOA)

Thư mục này dùng để lưu trữ các ảnh chụp màn hình minh chứng kết quả chạy và kiểm thử thực tế của bài thực hành cá nhân Buổi 4: **OpenAPI + Flask + Swagger UI**.

---

## Danh sách ảnh minh chứng cần thực hiện

| Tên file đề xuất | Nội dung minh chứng | Thao tác thực hiện |
| :--- | :--- | :--- |
| `01_terminal_run.png` | Khởi chạy Flask app thành công | Mở terminal, chạy lệnh `python3 app.py`, chụp lại log hiển thị cổng `5000` và 2 đường link `/openapi.json` và `/docs`. |
| `02_swagger_ui_overview.png` | Tổng quan giao diện Swagger UI | Mở trình duyệt tại `http://localhost:5000/docs`, chụp toàn cảnh trang hiển thị tiêu đề API, mô tả và các nhóm endpoint Books. |
| `03_openapi_json.png` | Nội dung đặc tả OpenAPI JSON | Mở trình duyệt hoặc Postman/cURL tại `http://localhost:5000/openapi.json`, chụp nội dung JSON chứa `openapi: 3.0.3`, `info`, `paths`, `components`. |
| `04_tryitout_get_books.png` | Thử nghiệm `GET /books` | Trên Swagger UI, mở mục `GET /books`, nhấn **Try it out** -> **Execute**, chụp lại Response Body mã `200` có danh sách dữ liệu, `pagination` và `_links`. |
| `05_tryitout_post_book.png` | Thử nghiệm `POST /books` | Trên Swagger UI, mở `POST /books`, nhấn **Try it out**, nhập JSON tạo sách mới, nhấn **Execute**, chụp Response Body mã `201` kèm Response Header `Location`. |
| `06_tryitout_get_book_id.png` | Thử nghiệm `GET /books/{bid}` | Trên Swagger UI, mở `GET /books/{bid}`, nhập `bid = 1`, nhấn **Execute**, chụp Response Body mã `200` kèm chi tiết cuốn sách. |
| `07_tryitout_patch_book.png` | Thử nghiệm `PATCH /books/{bid}` | Trên Swagger UI, mở `PATCH /books/{bid}`, cập nhật giá sách `{"price": 49.99}`, nhấn **Execute**, chụp Response Body mã `200`. |
| `08_tryitout_delete_book.png` | Thử nghiệm `DELETE /books/{bid}` | Trên Swagger UI, mở `DELETE /books/{bid}`, nhập `bid = 5`, nhấn **Execute**, chụp Response Code `204 No Content`. |
| `09_test_suite_passed.png` | Chạy bộ test tự động thành công | Chạy lệnh `python3 test_app.py`, chụp kết quả terminal báo `Ran 18 tests ... OK`. |

---

## Hướng dẫn chụp ảnh trên hệ điều hành Ubuntu / Linux

- **Chụp toàn màn hình:** Nhấn phím `PrtScn`.
- **Chụp một vùng màn hình:** Nhấn tổ hợp `Shift + PrtScn` hoặc sử dụng ứng dụng **Screenshot** / **GNOME Screenshot**.
- Lưu các file ảnh vào thư mục: `/home/tung/Desktop/SOA/api_session_04/screenshots/`
