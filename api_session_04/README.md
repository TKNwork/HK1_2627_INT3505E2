# BÀI THỰC HÀNH CÁ NHÂN BUỔI 4: OPENAPI + FLASK + SWAGGER UI

**Học phần:** Kiến trúc Hướng Dịch vụ (Service-Oriented Architecture - SOA)  
**Chủ đề:** Hệ sinh thái công cụ & Tích hợp Flask (Tool Ecosystem & Flask Integration)  
**Mã lớp:** INT3505E2  

---

## 1. Giới thiệu bài thực hành
Bài thực hành cá nhân Buổi 4 tập trung vào việc áp dụng chuẩn tài liệu hóa API công nghiệp (**OpenAPI Specification 3.0.3**) vào hệ sinh thái ứng dụng Web **Python Flask**. Dự án tích hợp công cụ tự động trích xuất đặc tả từ mã nguồn và nhúng giao diện tương tác **Swagger UI** trực tiếp vào ứng dụng, giúp lập trình viên và đối tác dễ dàng tra cứu, kiểm thử API mà không cần phụ thuộc vào tài liệu tĩnh bên ngoài.

---

## 2. Mục tiêu tích hợp Flask, OpenAPI và Swagger UI
1. **Tài liệu hóa tự động (Code-First to Spec):** Sử dụng các thư viện chuyên dụng để trích xuất cấu trúc dữ liệu, tham số và phản hồi của Flask route thành tài liệu OpenAPI JSON chuẩn xác.
2. **Chuẩn hóa mô hình dữ liệu:** Áp dụng **Marshmallow Schema** để định nghĩa kiểu dữ liệu (types), ràng buộc (validation) và tài liệu hóa các schema trong phần `components/schemas`.
3. **Cung cấp đặc tả máy đọc được (Machine-readable):** Endpoint `GET /openapi.json` trả về file cấu hình JSON chuẩn OpenAPI 3.0.3.
4. **Tương tác trực quan (Human-readable & Interactive):** Endpoint `GET /docs` nhúng giao diện **Swagger UI**, cho phép lập trình viên thử nghiệm trực tiếp từng phương thức HTTP (GET, POST, PUT, PATCH, DELETE) qua tính năng **Try it out**.

---

## 3. Khảo sát và lựa chọn Flask App tái sử dụng
Sau khi khảo sát các ứng dụng mẫu từ các buổi trước:
- `api_session_01`: Các ứng dụng cơ bản (`app1.py` đến `app6.py`), trong đó `app6.py` quản lý sách nhưng chưa có schema chặt chẽ, chưa hỗ trợ lọc, tìm kiếm hoặc phân trang chi tiết.
- `api_session_02`: `app3.py` triển khai **Books Management API** rất hoàn chỉnh với lưu trữ In-memory, hỗ trợ phân trang (Pagination), lọc theo tác giả (`author`), tìm kiếm theo từ khóa (`q`), phản hồi kèm HATEOAS links, cập nhật toàn bộ (PUT), cập nhật từng phần (PATCH) và xóa (DELETE).
- `api_session_03`: `app_orders.py` chỉ có phương thức `GET /orders` (Cursor pagination); `blog_api/app.py` mới có GET/POST và phụ thuộc module riêng.
- `Nhom_3/dist/tasks-api.yaml`: Là đặc tả YAML của bài tập nhóm lớn (Tasks API với Bearer JWT Auth), chưa có backend Python tương ứng trong các buổi trước.

👉 **Quyết định:** Tái sử dụng và nâng cấp **Books Management API** từ `api_session_02/app3.py`.  
**Lý do:**
- Đầy đủ các phương thức RESTful (GET danh sách, GET chi tiết, POST tạo mới, PUT cập nhật toàn bộ, PATCH cập nhật một phần, DELETE xóa).
- Dữ liệu in-memory tự sinh ban đầu, chạy độc lập, không phụ thuộc cơ sở dữ liệu bên ngoài, dễ dàng chạy và kiểm thử trên mọi môi trường.
- Phù hợp hoàn hảo để ánh xạ vào Marshmallow Schemas và minh họa chức năng Try It Out trên Swagger UI mà không gặp lỗi kết nối hay thiếu endpoint.

---

## 4. Lý do lựa chọn thư viện `apispec`
Dự án sử dụng bộ công cụ **`apispec`** kết hợp **`marshmallow`** đúng theo nội dung slide bài giảng Buổi 4:
1. **Tính linh hoạt cao:** `apispec` cùng hai plugin cốt lõi:
   - `FlaskPlugin` (từ `apispec-webframeworks`): Tự động phân tích đường dẫn Flask route, path parameters `<int:bid>` chuyển thành `{bid}` trong OpenAPI.
   - `MarshmallowPlugin` (từ `apispec.ext.marshmallow`): Tự động chuyển đổi các class Marshmallow Schema thành các OpenAPI Components Schemas chuẩn xác.
2. **Không xâm lấn kiến trúc ứng dụng (Non-invasive):** Không ép buộc phải viết lại toàn bộ cấu trúc view function như một số framework nặng nề khác, giữ nguyên code Flask trong sáng, dễ đọc.
3. **So với `flask-smorest`:** `flask-smorest` đóng gói sâu vào tầng routing và validation (yêu cầu kế thừa `MethodView` và ép kiểu tự động). Sử dụng `apispec` thuần túy giúp sinh viên nắm vững nguyên lý hoạt động của từng thành phần: Schema -> Spec Generator -> JSON Endpoint -> Swagger UI Renderer.

---

## 5. Cấu trúc thư mục dự án

```text
api_session_04/
├── app.py                  # Entry point chính: Flask routes, in-memory DB, đăng ký apispec
├── schemas.py              # Định nghĩa các Marshmallow Schema (Data model, validation)
├── openapi.py              # Cấu hình APISpec 3.0.3 và template nhúng giao diện Swagger UI
├── test_app.py             # Bộ test tự động toàn diện kiểm thử OpenAPI và CRUD API
├── requirements.txt        # Danh sách các thư viện Python phụ thuộc
├── .gitignore              # Bỏ qua file tạm, môi trường ảo, cache
├── README.md               # Tài liệu hướng dẫn chi tiết dự án (file này)
└── screenshots/            # Thư mục lưu trữ ảnh chụp màn hình minh chứng
    └── README.md           # Bảng phân công và hướng dẫn chụp từng ảnh minh chứng
```

---

## 6. Hướng dẫn cài đặt môi trường (Python Dependencies)

### Yêu cầu tiên quyết
- Hệ điều hành: Ubuntu 22.04 / 24.04 LTS (hoặc Linux tương đương).
- Python 3.10+ (đã tích hợp sẵn `python3-venv` và `pip`).

### Các bước cài đặt

1. Mở Terminal và di chuyển vào thư mục bài thực hành:
   ```bash
   cd /home/tung/Desktop/SOA/api_session_04
   ```

2. Tạo và kích hoạt môi trường ảo Python (khuyên dùng):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Cài đặt các gói phụ thuộc từ `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

---

## 7. Hướng dẫn khởi chạy ứng dụng trên Ubuntu

1. Chạy server Flask:
   ```bash
   python3 app.py
   ```

2. Terminal sẽ hiển thị thông báo sẵn sàng:
   ```text
   ============================================================
   🚀 Khởi chạy Books Management API (SOA Buổi 4)
   📖 OpenAPI Specification: http://localhost:5000/openapi.json
   🌐 Swagger UI Documentation: http://localhost:5000/docs
   ============================================================
    * Serving Flask app 'app'
    * Debug mode: on
    * Running on all addresses (0.0.0.0)
    * Running on http://127.0.0.1:5000
   ```

---

## 8. Các đường dẫn quan trọng

| Đường dẫn | Phương thức | Mô tả |
| :--- | :---: | :--- |
| `http://localhost:5000/` | `GET` | Tự động chuyển hướng (Redirect 302) đến `/docs`. |
| `http://localhost:5000/docs` | `GET` | Giao diện tài liệu tương tác **Swagger UI**. *(Cần kết nối mạng để tải tài nguyên CDN `unpkg.com`)* |
| `http://localhost:5000/openapi.json` | `GET` | Tệp đặc tả OpenAPI Specification 3.0.3 dạng JSON nguyên bản. |

---

## 9. Danh sách các API Endpoint được triển khai

| Endpoint | Method | Tag | Chức năng & Mô tả | Mã HTTP Status |
| :--- | :---: | :---: | :--- | :---: |
| `/books` | `GET` | Books | Lấy danh sách sách có phân trang (`page`, `size`), lọc theo tác giả (`author`), tìm kiếm (`q`). Kèm `Cache-Control` và HATEOAS links. | `200`, `400` |
| `/books` | `POST` | Books | Tạo sách mới. Yêu cầu JSON có `title` và `author`. Trả về đối tượng vừa tạo kèm header `Location: /books/{id}`. | `201`, `400`, `415` |
| `/books/{bid}` | `GET` | Books | Lấy chi tiết cuốn sách theo ID. Kèm header `Cache-Control: max-age=60`. | `200`, `404` |
| `/books/{bid}` | `PUT` | Books | Thay thế toàn bộ thông tin sách. Yêu cầu bắt buộc đủ `title` và `author`. | `200`, `404`, `422` |
| `/books/{bid}` | `PATCH` | Books | Cập nhật một phần thuộc tính (`title`, `author`, `isbn`, `price`). Kiểm tra `price >= 0`. | `200`, `404`, `422` |
| `/books/{bid}` | `DELETE` | Books | Xóa cuốn sách tương ứng khỏi hệ thống. | `204`, `404` |

---

## 10. Hướng dẫn kiểm thử bằng Swagger UI (Try it out)

1. Mở trình duyệt web và truy cập: `http://localhost:5000/docs`.
2. **Kiểm thử `GET /books`:**
   - Nhấp vào hàng **GET /books**.
   - Nhấn nút **Try it out** ở góc phải.
   - Nhập tham số tùy chọn (ví dụ: `q = Clean` hoặc `author = Robert C. Martin`).
   - Nhấn **Execute**. Quan sát Response Code `200` và danh sách JSON trả về kèm phần `pagination`.
3. **Kiểm thử `POST /books`:**
   - Nhấp vào **POST /books**, nhấn **Try it out**.
   - Trong ô Request body, nhập:
     ```json
     {
       "title": "Clean Code in Python",
       "author": "Mariano Anaya",
       "isbn": "9781800560215",
       "price": 39.99
     }
     ```
   - Nhấn **Execute**, kiểm tra Response Code `201 Created` và Response Header có `Location: /books/5`.
4. **Kiểm thử `GET /books/{bid}`:**
   - Nhấp vào **GET /books/{bid}**, nhập `bid = 1`, nhấn **Execute** -> nhận về thông tin sách Clean Code.
5. **Kiểm thử `PATCH /books/{bid}`:**
   - Nhấp vào **PATCH /books/{bid}**, nhập `bid = 1`, truyền body `{"price": 49.99}` -> nhận về mã `200` với giá đã cập nhật.
6. **Kiểm thử `DELETE /books/{bid}`:**
   - Nhấp vào **DELETE /books/{bid}**, nhập `bid = 5`, nhấn **Execute** -> nhận về mã `204 No Content`.
   - Thực hiện lại lệnh GET với `bid = 5` để kiểm chứng trả về mã `404 Not Found`.

---

## 11. Hướng dẫn chạy bộ kiểm thử tự động (Unit Test)

Dự án cung cấp bộ test tự động gồm 18 ca kiểm thử bao phủ toàn bộ các case thành công và xử lý ngoại lệ:
```bash
python3 test_app.py
```
Kết quả mong đợi:
```text
----------------------------------------------------------------------
Ran 18 tests in 0.020s

OK
```

---

## 12. Danh sách ảnh minh chứng cần nộp

Vui lòng chụp và lưu các ảnh màn hình vào thư mục `screenshots/` theo hướng dẫn tại [screenshots/README.md](screenshots/README.md):
1. `01_terminal_run.png`: Terminal khởi chạy ứng dụng Flask thành công.
2. `02_swagger_ui_overview.png`: Toàn cảnh Swagger UI tại `http://localhost:5000/docs`.
3. `03_openapi_json.png`: Trình duyệt hiển thị dữ liệu JSON từ `http://localhost:5000/openapi.json`.
4. `04_tryitout_get_books.png`: Kết quả Execute phương thức `GET /books`.
5. `05_tryitout_post_book.png`: Kết quả Execute phương thức `POST /books` mã 201 + Location header.
6. `06_tryitout_get_book_id.png`: Kết quả Execute `GET /books/{bid}` mã 200.
7. `07_tryitout_patch_book.png`: Kết quả Execute `PATCH /books/{bid}` mã 200.
8. `08_tryitout_delete_book.png`: Kết quả Execute `DELETE /books/{bid}` mã 204.
9. `09_test_suite_passed.png`: Kết quả chạy lệnh `python3 test_app.py` đạt 18/18 tests OK.
