# SOA – Bài tập Buổi 7: Product và Order API

Bài làm độc lập trong `api_session_07/homework-buoi-7`, chuẩn bị nộp **trước Buổi 8**.
Không tìm thấy Product API cũ phù hợp để tái sử dụng; triển khai mới.
Không sửa Bookstore buổi 5 hay bài auth buổi 6. Không tìm thấy `SOA - B7 - Backend_Service.pdf`
trong workspace/tài liệu đính kèm khi thực hiện; yêu cầu người học gửi là nguồn đặc tả chính.
Không khẳng định đã đối chiếu trang 22–26 hoặc trang 40 của slide.

## 1. Phạm vi và stack

Hoàn thành yêu cầu bắt buộc: sáu endpoint Product, blueprint orders riêng với OrderItem,
Dockerfile/Compose, `/healthz`, `/ready`, pytest cho POST và GET dùng eager loading.
Bổ sung migration, validation, OpenAPI code-first, log JSON, test N+1 và hướng dẫn nộp bài.
Chưa commit/push vì cần xác nhận của người học. Không có frontend, auth, thanh toán hay queue.

Python 3.12; Flask 3.1; Flask-SQLAlchemy 3.1; SQLAlchemy 2.0 typed;
Marshmallow 4; Flask-Smorest 0.46.1–0.47; Flask-Migrate 4; PostgreSQL 16;
psycopg 3; Gunicorn 23; pytest. `pyproject.toml` là nơi duy nhất khai báo dependency,
có giới hạn phiên bản; không duy trì thêm requirements.txt. Các khoảng phiên bản không phải lockfile.
Đã cài thực tế, chạy `pip check` và test với các phiên bản ghi trong `docs/test-results.md`.
Flask-Smorest hỗ trợ Marshmallow 4 từ 0.46.1 theo
[changelog chính thức](https://flask-smorest.readthedocs.io/en/latest/changelog.html).
Phong cách ORM theo [Flask-SQLAlchemy 3.1 Quick Start](https://flask-sqlalchemy.palletsprojects.com/en/stable/quickstart/).

```text
homework-buoi-7/
├── README.md, pyproject.toml, .env.example, .gitignore, .dockerignore
├── Dockerfile, docker-compose.yml, wsgi.py, gunicorn.conf.py
├── migrations/                  # Revision đã xem lại, có upgrade/downgrade
├── src/product_api/
│   ├── factory.py, config.py, extensions.py, errors.py, logging_config.py
│   ├── models/                 # Product, Order, OrderItem
│   ├── schemas/                # Input/output/patch/reserve/pagination
│   ├── api/                    # Blueprint products/orders/health
│   └── services/               # Nghiệp vụ và transaction
├── tests/                      # Database tạm riêng cho mỗi test
└── docs/test-results.md
```

## 2. Mô hình và quyết định thiết kế

`Order 1 → N OrderItem N ← 1 Product`. Order không có product_id đơn lẻ.
OrderItem chứa FK, quantity và **unit_price_cents lịch sử**; tổng đơn là tổng
`quantity × unit_price_cents`. Product lồng trong response thể hiện dữ liệu hiện tại,
có thể khác giá lịch sử hoặc đã archived; xóa mềm không phá đơn cũ.
Có unique SKU, unique (order_id, product_id), FK, index và CHECK giá/tồn kho/số lượng.
SQLite bật `PRAGMA foreign_keys=ON`.

Các quy tắc sau là lựa chọn thiết kế bổ sung:

- SKU trim, viết hoa, 3–32 ký tự, chỉ `[A-Z0-9][A-Z0-9_-]*`; tên trim, 1–255 ký tự.
  Description tối đa 4000 ký tự. SKU đã archived vẫn giữ unique và không tái sử dụng.
- Input JSON số nguyên phải là integer thực sự; từ chối boolean, float, chuỗi và null.
  Giá/tồn kho tối đa 2,147,483,647 để phù hợp PostgreSQL INTEGER.
- Từ chối field lạ bằng 422; không cho ghi id, archived, timestamps qua input thông thường.
  PATCH cho sửa SKU/name/description/price_cents/qty_in_stock; body rỗng trả 422.
  Field vắng mặt giữ nguyên, description có thể được đặt null.
- List sắp id tăng dần, page mặc định 1, size 20 (tối đa 100).
  Page vượt phạm vi trả 200 với items rỗng, total không đổi; query lạ trả 422.
- DELETE lần đầu 204 không body; lần sau 404. Product archived không xuất hiện ở
  list/get/patch/reserve. Các response đơn cũ vẫn có thể chứa product archived.
- Một đơn có 1–100 items; product_id trùng bị từ chối bằng 422, không tự gộp.
  Product không tồn tại hoặc archived trả 404 `product_not_found`.
- Tạo đơn **không tự giảm tồn kho**. Đây là đơn giản hóa phục vụ bài học, chưa phải
  quy trình đặt hàng production hoàn chỉnh. Reserve riêng trả 200 với Product và tồn kho mới.

## 3. Endpoint và lỗi

| Method | Đường dẫn | Thành công | Lỗi chính |
|---|---|---|---|
| GET | `/api/v1/products?page=1&size=20` | 200, items/page/size/total | 422 |
| GET | `/api/v1/products/{id}` | 200 | 404 |
| POST | `/api/v1/products` | 201 | 409 duplicate_sku, 422 |
| POST | `/api/v1/products/{id}/reserve` | 200 | 404, 409 insufficient_stock, 422 |
| PATCH | `/api/v1/products/{id}` | 200 | 404, 409 duplicate_sku, 422 |
| DELETE | `/api/v1/products/{id}` | 204, không body | 404 |
| POST | `/api/v1/orders` | 201, nested items | 404 product_not_found, 422 |
| GET | `/api/v1/orders?page=1&size=20` | 200, nested items/page/size/total | 422 |
| GET | `/api/v1/orders/{id}` | 200, nested items | 404 order_not_found |
| GET | `/healthz` | 200 alive | Không query DB |
| GET | `/ready` | 200 ready | 503 not_ready |

Lỗi thống nhất: `{"error":"validation_error","detail":"…","fields":{…},"request_id":"…"}`.
`fields` chỉ có khi có lỗi từng trường. Mã lỗi dùng tiếng Anh.
400 `bad_request`: JSON hỏng; 404 `not_found`: route không tồn tại;
405 `method_not_allowed` (giữ header Allow); 415 `unsupported_media_type`: POST/PATCH
không có Content-Type JSON; 422 `validation_error`: JSON hợp lệ sai schema.
Lỗi nghiệp vụ có các code cụ thể trong bảng. 500 `internal_error` không lộ SQL,
stack trace, credential; log ghi loại lỗi và vị trí frame để tra cứu, bỏ exception message
vì message DB có thể chứa chuỗi kết nối/dữ liệu. Request ID do server tạo.
Spec code-first tại `/openapi.json`, OpenAPI **3.0.3**; Swagger UI tại `/docs`.
UI lấy JavaScript/CSS từ CDN nên cần Internet; spec và API chạy độc lập CDN.
Không có bản YAML viết tay cần đồng bộ.

## 4. Transaction, reserve và eager loading

Reserve dùng một `UPDATE ... WHERE id=:id AND archived=false AND qty_in_stock>=:qty`
với `qty_in_stock=qty_in_stock-:qty RETURNING id`. Database kiểm tra và trừ trong
cùng statement; không dùng đọc–trừ–commit. Khi hai request cùng reserve, điều kiện
được database kiểm tra với phiên bản hàng được cập nhật; CHECK là lớp bảo vệ bổ sung.
Nếu không cập nhật được, kiểm tra active product để phân biệt 404 và 409.

SKU unique được enforce ở database. Khi IntegrityError, rollback rồi chỉ ánh xạ
constraint `uq_products_sku` hoặc SQLite UNIQUE products.sku sang 409;
constraint khác vẫn là 500, không bị gắn nhầm duplicate_sku.

Tạo đơn lấy Product và giá từ database (PostgreSQL dùng FOR SHARE theo id tăng dần),
kiểm tra đủ product, tạo Order và toàn bộ OrderItem rồi commit một lần. Flush lấy id
không phải commit. Bất kỳ lỗi nào đều rollback; test còn ép lỗi lúc INSERT item để
chứng minh không để lại Order dở dang. Tạo đơn không tin giá client gửi.

GET orders dùng `selectinload(Order.items).joinedload(OrderItem.product)` ngay tại query:
query Orders riêng, query items JOIN Product riêng. Collection dùng selectinload nên
không cần `.unique()` cho query Orders. Các relationship đặt `lazy="raise"` để serializer
quên eager load sẽ gây lỗi thay vì âm thầm tạo query mỗi hàng.
Trên dữ liệu thử 2 và 8 đơn, mỗi đơn 3 items: list có **3 SELECT**
(COUNT phân trang + Orders + items JOIN Product), detail có **2 SELECT**.
Listener chỉ đếm trong request, dùng session mới và tháo trong finally.
Không khẳng định 3 query đúng với mọi kích thước: selectinload có thể chia batch IN.

## 5. Chạy local và migration

Từ thư mục bài tập, dùng shell Linux/macOS và Python 3.12:

```bash
cd api_session_07/homework-buoi-7  # nếu đang ở root repository SOA
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
flask --app wsgi:app db upgrade
gunicorn -c gunicorn.conf.py wsgi:app
```

Nếu đang trong `api_session_07`, chỉ `cd homework-buoi-7`.
Mặc định SQLite nằm ở `instance/products.db` trong thư mục hiện tại; factory tạo thư mục
instance nhưng **không create_all**. Flask CLI đọc `.env`; Gunicorn trực tiếp dùng mặc định
hoặc biến đã export. Để Gunicorn đọc cấu hình tùy chỉnh trong `.env`, có thể dùng:

```bash
set -a
source .env
set +a
flask --app wsgi:app db upgrade
gunicorn -c gunicorn.conf.py wsgi:app
```

Chỉ source `.env` do chính bạn quản lý. Đổi PostgreSQL local bằng biến môi trường
`DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/DB` trước migrate và chạy.
Không commit giá trị thật. Config PostgreSQL có connect_timeout 3 giây, pool_timeout 5 giây,
statement_timeout 5 giây và pool_pre_ping; không áp các option đó lên SQLite.
`PORT`, `WEB_CONCURRENCY`, `LOG_LEVEL` chỉnh qua environment.

Migration mới hoàn toàn: `flask --app wsgi:app db upgrade`.
Kiểm tra: `flask --app wsgi:app db current` và `flask --app wsgi:app db check`.
Khi chính bạn thay model sau này, tạo revision bằng `flask --app wsgi:app db migrate -m '…'`,
xem lại revision rồi upgrade. Không chạy migrate tự sinh revision lúc container start.

## 6. Docker Compose

Yêu cầu máy đích có Docker Engine đang chạy và Compose v2 hỗ trợ dependency conditions.
Từ thư mục bài tập:

```bash
docker compose config
docker compose up --build
```

Không cần sửa source, tạo .env hay connection string cho cấu hình Compose mẫu.
DB hostname là `db`, không phải localhost. PostgreSQL có healthcheck và named volume `pgdata`.
Service `migrate` đợi DB healthy, chạy revision đã có và thoát 0; API đợi migrate thành công,
sau đó Gunicorn mới phục vụ. Hai worker không tự chạy migration.
Image multi-stage, cài wheel từ cùng pyproject, chạy UID 10001 và có instance directory
được cấp quyền ghi. API xuất port 8000, DB không publish port ra host.
Credential `soa/local-only-password` chỉ là mẫu local, không phải cấu hình production.

```bash
docker compose ps
docker compose logs api migrate db
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/ready
docker compose down
```

`down` giữ dữ liệu volume; không chạy lệnh xóa volume. Mỗi lần migrate one-shot cần chạy lại
khi nâng revision; khi thay đổi schema, dừng stack bằng `docker compose down` rồi
`docker compose up --build` để migrate hoàn tất trước API. Không hỗ trợ rolling deployment.
Môi trường làm bài không có Docker trong PATH: chưa xác minh Compose config/build/run.

## 7. Ví dụ curl chạy nối tiếp

Mở terminal thứ hai khi API đang chạy. Cần curl và Python 3 (không cần jq).
Ví dụ lấy ID từ response, chạy trên DB mới đã migrate. SKU demo phải chưa tồn tại;
chạy lại trên cùng DB dùng SKU khác vì SKU archived vẫn unique.

```bash
BASE=http://localhost:8000
A=$(curl --fail-with-body -sS -X POST "$BASE/api/v1/products" \
  -H 'Content-Type: application/json' \
  -d '{"sku":"DEMO-A","name":"Keyboard","price_cents":12000,"qty_in_stock":10}')
printf '%s\n' "$A"
A_ID=$(printf '%s' "$A" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
B=$(curl --fail-with-body -sS -X POST "$BASE/api/v1/products" \
  -H 'Content-Type: application/json' \
  -d '{"sku":"DEMO-B","name":"Mouse","price_cents":5000,"qty_in_stock":20}')
B_ID=$(printf '%s' "$B" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl --fail-with-body -sS -X POST "$BASE/api/v1/products/$A_ID/reserve" \
  -H 'Content-Type: application/json' -d '{"qty":2}'
ORDER=$(curl --fail-with-body -sS -X POST "$BASE/api/v1/orders" \
  -H 'Content-Type: application/json' \
  -d "{\"items\":[{\"product_id\":$A_ID,\"quantity\":2},{\"product_id\":$B_ID,\"quantity\":1}]}")
ORDER_ID=$(printf '%s' "$ORDER" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl --fail-with-body -sS "$BASE/api/v1/orders/$ORDER_ID"
curl --fail-with-body -sS "$BASE/api/v1/orders?page=1&size=20"
curl --fail-with-body -sS "$BASE/api/v1/products?page=1&size=20"
```

Tổng đơn demo là 29.000 cents. Sau reserve tồn kho A là 8; tạo đơn không trừ tiếp.

## 8. Test, health và log

```bash
source .venv/bin/activate
pip check
pytest -q
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/ready
curl -sS http://localhost:8000/openapi.json
```

Pytest dùng SQLite file trong tmp_path riêng từng test, dựng schema bằng migration thật;
không đọc DATABASE_URL thật và không chạm dữ liệu ứng dụng. Bao phủ POST, validation,
SKU duplicate, PATCH, soft delete, reserve, order snapshot/atomicity, eager loading,
health/readiness, lỗi protocol, OpenAPI và log.
Kết quả thực tế, phiên bản và giới hạn ở [docs/test-results.md](docs/test-results.md).

`/healthz` không query DB. `/ready` chạy `SELECT 1`, 503 khi lỗi dependency,
không trả exception nội bộ. `SELECT 1` chỉ chứng minh kết nối, **không chứng minh schema đã migrate**.
Log ứng dụng mỗi request một dòng JSON: timestamp UTC, level, message, request_id,
method, path, status_code, latency_ms. Xem stdout local hoặc `docker compose logs api`.
Không log body, password hoặc database URL mặc định. Log khởi động Gunicorn/Alembic
là log vận hành của công cụ và có thể không dùng JSON formatter ứng dụng.

## 9. Giải thích ngắn để trình bày

| Câu hỏi | Giải thích |
|---|---|
| Application Factory? | Tạo nhiều app với config khác nhau, tách test DB và production; tránh khởi tạo phụ thuộc lúc import. |
| Blueprint khác app? | Blueprint gom route theo resource; chỉ hoạt động khi được đăng ký vào Flask app. |
| Model / Schema / Resource? | Model lưu và quan hệ DB; Schema validate/serialize; Resource nhận HTTP, gọi nghiệp vụ và trả response. |
| Vì sao cần OrderItem? | Một đơn có nhiều sản phẩm; mỗi dòng có số lượng và giá riêng, Product có thể nằm trong nhiều đơn. |
| N+1 là gì? | Query danh sách rồi query quan hệ riêng từng dòng; số query tăng theo số bản ghi. Eager loading tải trước theo nhóm. |
| selectinload / joinedload? | selectinload dùng query phụ với IN, tránh nhân bản hàng Order; joinedload JOIN cùng query. Collection joinedload cần unique() khi lấy ORM result. |
| Vì sao rollback? | Hủy mọi ghi của nghiệp vụ thất bại và phục hồi session sau lỗi transaction, tránh đơn dở dang. |
| Migration / create_all? | Migration có lịch sử phiên bản, thay đổi schema và review được; create_all chỉ tạo bảng thiếu, không nâng cấp cấu trúc đã tồn tại. |
| healthz / ready? | healthz kiểm tra process; ready kiểm tra DB. Process còn sống vẫn có thể chưa sẵn sàng. |
| Gunicorn? | WSGI server quản lý worker và phục vụ deployment; Flask dev server dành cho phát triển. |
| Reserve đồng thời? | Hai request cùng đọc tồn kho có thể cùng thành công sai; conditional UPDATE kiểm tra và trừ nguyên tử. |
| Snapshot giá? | Giá Product có thể đổi, nhưng tổng đơn lịch sử phải phản ánh giá tại thời điểm tạo. |

## 10. Nộp bài bằng Git

Nộp toàn bộ thư mục này **trừ** `.venv`, `.env`, database, cache, egg-info, instance.
Các file migrations, src, tests, docs, Docker/config và README phải có trong repo.
Repository cha hiện tại là `/home/tung/Desktop/SOA`, branch `main`, remote
`git@github.com:TKNwork/HK1_2627_INT3505E2.git`; khi bắt đầu branch đã ahead 1 commit
và có `Nhom_3/` chưa theo dõi. Không đổi remote/branch, không stage bài cũ.
Remote có tên lớp/nhóm nên cần kiểm tra repo cá nhân trước khi push.

Nếu repo này đúng là repo cá nhân bạn muốn nộp, thực hiện sau khi review:

```bash
cd /home/tung/Desktop/SOA
git status --short
git add -- api_session_07/homework-buoi-7
git diff --cached --stat
git diff --cached --name-only
# Chỉ commit khi staged files đúng phạm vi dự kiến của bạn.
git commit -m "feat: complete SOA session 7 product and order backend"
git push origin main
```

Lưu ý: push main cũng đẩy commit cũ đang ahead; kiểm tra `git log origin/main..main`
trước khi quyết định. Nếu đây là repo nhóm, **không đổi remote nhóm**. Tạo một repo cá nhân
trống trên GitHub, clone vào thư mục khác bên ngoài SOA rồi chỉ chép bài 7:

```bash
# Thay URL bằng repo cá nhân đã tạo; chạy từ một thư mục ngoài repo SOA.
git clone YOUR_PERSONAL_REPOSITORY_URL soa-session7-personal
cd soa-session7-personal
mkdir -p homework-buoi-7
# GNU tar: bỏ toàn bộ môi trường, DB và cache của máy làm bài.
tar -C /home/tung/Desktop/SOA/api_session_07/homework-buoi-7   --exclude=.venv --exclude=.env --exclude=instance --exclude=__pycache__   --exclude=.pytest_cache --exclude='*.egg-info' --exclude='*.db'   --exclude='*.sqlite*' --exclude=build --exclude=dist -cf - .   | tar -C homework-buoi-7 -xf -
git add -- homework-buoi-7
git diff --cached --stat
git commit -m "feat: complete SOA session 7 product and order backend"
git push -u origin HEAD
```

Không tạo Git repo lồng trong SOA. Các lệnh commit/push ở trên là hướng dẫn,
**chưa được tự động thực hiện**. Bước nộp qua repo cá nhân còn chờ bạn xác nhận và thực hiện.
