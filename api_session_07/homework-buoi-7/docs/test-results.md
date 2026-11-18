# Kết quả kiểm tra thực tế – SOA Buổi 7

Ngày **03/11/2026**, múi giờ Asia/Ho_Chi_Minh. Python **3.12.3**.
Không tìm thấy slide PDF buổi 7; đặc tả lấy từ yêu cầu đính kèm của người học.

## Dependency và đóng gói

Cài thành công `pip install --no-cache-dir -e '.[test]'` trong .venv riêng.
Lần đầu DNS sandbox lỗi `[Errno -2] Name or service not known`; thử lại qua quyền
mạng của công cụ thành công. `pip check`: **No broken requirements found**.

| Package | Phiên bản đã chạy |
|---|---|
| Flask | 3.1.3 |
| Flask-SQLAlchemy / SQLAlchemy | 3.1.1 / 2.0.55 |
| marshmallow / flask-smorest | 4.3.1 / 0.47.0 |
| Flask-Migrate / Alembic | 4.1.0 / 1.20.1 |
| psycopg / psycopg-binary | 3.3.7 / 3.3.7 |
| Gunicorn / pytest | 23.0.0 / 9.2.0 |

Build wheel của project thành công. Cài wheel bằng `pip install --no-deps --target`
vào thư mục tạm, import đúng module từ wheel, tạo app và gọi /healthz thành công.
Cách này dùng chung dependency venv đã cài, không phải build Docker image.
Khoảng dependency trong pyproject không phải lockfile.

## Pytest đã chạy

Lệnh: `.venv/bin/pytest -q`.

```text
.............................................................            [100%]
61 passed in 4.49s
```

**61 passed / 0 failed / 0 skipped** ở lần chạy cuối. Các lỗi phát hiện trong lúc
phát triển đã sửa trước kết quả này. Test dùng SQLite file riêng từng tmp_path,
dựng bằng migration thật, bật foreign keys; không chạm database của người học.

Bao phủ POST Product/Order, chuẩn hóa SKU/tên, strict integer, duplicate SKU,
unknown/server fields, lỗi JSON 400/media type 415/method 405/route 404,
pagination/total, PATCH, soft delete, reserve, order snapshot/giá DB,
order atomicity (cả lỗi trước ghi và lỗi INSERT item), eager loading,
health/readiness 200/503, 500 không lộ nội bộ, log JSON, OpenAPI và DB constraints.
Readiness 503 được kiểm tra bằng lỗi kết nối giả lập, không mô phỏng server PostgreSQL thật.

### N+1

Listener SQLAlchemy chỉ đếm SELECT trong GET, xóa session trước request,
tháo listener trong finally; không mock ORM và không tính query tạo fixture.

| Dữ liệu | GET danh sách | GET chi tiết |
|---|---:|---:|
| 2 orders, mỗi order 3 items | 3 SELECT | — |
| 8 orders, mỗi order 3 items | 3 SELECT | 2 SELECT |

List gồm COUNT + SELECT Orders + SELECT OrderItems JOIN Products.
Chiến lược `selectinload(Order.items).joinedload(OrderItem.product)`;
relationship lazy="raise" giúp phát hiện serializer quên load.
Kết quả chỉ áp dụng bộ dữ liệu nhỏ đã thử; selectinload có thể chia batch IN khi dữ liệu lớn.

## Migration

Revision **f10e6ef6245a** đã sinh và đọc lại: thứ tự bảng, FK, indexes, unique,
CHECK và downgrade. Test và luồng ứng dụng không dùng create_all.

| Kiểm tra | Kết quả |
|---|---|
| SQLite mới: upgrade đến head | Thành công |
| SQLite: flask db check | No new upgrade operations detected |
| SQLite tạm: upgrade → downgrade base → upgrade | Thành công; chỉ DB tạm |
| SQLite FK/check/index và ghi SQL sai | Pytest đã kiểm chứng |
| PostgreSQL: db upgrade --sql offline | Sinh DDL thành công |
| Migration trên PostgreSQL server | **Chưa kiểm tra** |
| Reserve concurrent trên PostgreSQL | **Chưa kiểm tra** |

Không tìm thấy postgres/psql trong PATH. Sinh SQL offline không tương đương
chạy migration hay kiểm tra hành vi server PostgreSQL. SQLite test không đủ
chứng minh PostgreSQL concurrency.

## Gunicorn và HTTP thật

Sandbox ban đầu chặn bind socket `[Errno 1] Operation not permitted`.
Chạy lại ngoài sandbox với Gunicorn 23, hai worker, **127.0.0.1:18007** và
SQLite riêng `/tmp/soa7-http.db` đã migrate. Server đã dừng sau kiểm tra.

- Chạy chuỗi curl phần 7 README, chỉ thay BASE sang port 18007.
- Tạo hai Product DEMO-A/DEMO-B, reserve A, tạo đơn hai items.
- Đọc lại xác nhận total_cents=29000; tất cả curl --fail-with-body thành công.
- /healthz, /ready, /docs, /openapi.json đều trả HTTP 200.
- Log request JSON có timestamp UTC, level, message, request_id, method, path,
  status_code và latency_ms; không log body hoặc database URL.

Đây là HTTP local qua Gunicorn với SQLite, **không phải HTTP trong container**.
Swagger UI HTML trả 200; chưa kiểm tra render JavaScript CDN bằng trình duyệt.

## Docker và các mức xác minh

| Mức | Trạng thái |
|---|---|
| Dockerfile / Compose / ignore / env mẫu | Đã tạo và rà soát nội dung |
| docker compose config | Chưa chạy được: `/bin/bash: docker: command not found` |
| Build image | Chưa kiểm tra |
| Run PostgreSQL/migrate/API container | Chưa kiểm tra |
| HTTP qua container | Chưa kiểm tra |
| HTTP local Gunicorn | Thành công như trên |

Trên máy có Docker, từ thư mục bài tập:

```bash
docker compose config
docker compose up --build
# Terminal khác:
docker compose ps
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/ready
docker compose logs api migrate db
```

Credential Compose là mẫu local. Không chạy lệnh xóa volume.
/ready dùng SELECT 1, chỉ chứng minh kết nối, không chứng minh schema đã migrate.

## Git và phạm vi

Chỉ tạo `api_session_07/homework-buoi-7`; tracked diff của bài cũ không đổi.
Không tìm thấy Product API cũ để tái sử dụng; Bookstore/auth cũ được giữ nguyên.
Đã kiểm tra git status, git diff --check, whitespace file mới và ignore.
.env, .venv, database, cache, build, egg-info được ignore; .env.example được nộp.
Chưa stage/commit/push, chưa tạo PR, không đổi remote/branch hoặc lịch sử.
Repo cha main đã ahead origin/main 1 commit trước khi bắt đầu; Nhom_3 vẫn untracked.
Bước nộp repo cá nhân **chưa hoàn tất**; lệnh và lưu ý ở README phần 10.
