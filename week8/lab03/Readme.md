# Lab 3 — Kiểm thử Books API bằng Newman

Collection books-api.postman_collection.json có 5 request happy path và
2 request lỗi. POST tạo sách lưu book_id để GET, PUT và DELETE dùng cùng ID.

## Yêu cầu

- Python và Node.js.
- Môi trường .venv trong lab08-starter đã cài các gói từ requirements.txt.

## 1. Khởi động Flask

Mở CMD từ thư mục `week8`.

```cmd
cd lab08-starter
.venv\Scripts\python.exe -m app --port 5000
```

Giữ cửa sổ này mở khi chạy Newman.

## 2. Chạy Newman

Mở cửa sổ CMD thứ hai từ thư mục `week8`.

```cmd
cd lab03
npx --yes newman run books-api.postman_collection.json -e ..\lab08-starter\postman\local.postman_environment.json -r cli,junit --reporter-junit-export junit.xml
```

## 3. Kiểm tra kết quả

Báo cáo được lưu tại [junit.xml](junit.xml). Lần chạy đã kiểm tra có **7 request, 15 assertion pass, 0 lỗi**, trong **513 ms**.

- POST thiếu `title` trả HTTP `400` và code `VALIDATION_ERROR`.
- `GET /books/9999` trả HTTP `404` và code `NOT_FOUND`.
