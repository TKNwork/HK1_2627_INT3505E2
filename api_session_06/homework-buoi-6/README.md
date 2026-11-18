# SOA – Buổi 6: Authentication và Authorization

Bài tập thiết kế hợp đồng API mạng xã hội đơn giản. Hạn theo đề: **trước Buổi 7**, chưa có ngày cụ thể. Tài liệu viết bằng tiếng Việt, field/scope/error code dùng tiếng Anh.

## Phạm vi chính thức và bổ sung

Theo đề được cung cấp: viết OpenAPI cho `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`, làm rõ scope, lỗi và HTTP status; kèm `SecurityAudit.md` tối thiểu 5 điểm và commit khi nộp. Bài này có 10 điểm audit. README, ma trận quyền, checklist, TTL, JWT profile, rotation và script kiểm tra là phần bổ sung để hợp đồng có thể kiểm tra được.

Không tìm thấy `SOA - B6_Auth.pdf` trong `/home/tung/Desktop/SOA` hoặc tệp đính kèm khi kiểm tra. **Chưa đọc slide**, không khẳng định nội dung ngoài prompt là yêu cầu của giảng viên.

Repository gốc là `/home/tung/Desktop/SOA`, nhánh hiện tại `main`, remote `origin`. Buổi 5 là Bookstore API. Đã đọc tĩnh `api_session_03/blog_api/app.py`: có `/api/v1/posts/<int:post_id>` với `id/title/content/user_id`, chưa có auth/visibility; không phù hợp trực tiếp với hợp đồng buổi 6. Bài này là thiết kế độc lập, dùng `author_id`, không tuyên bố tương thích với API blog cũ. Không sửa hoặc chạy backend cũ; không tạo repository lồng nhau.

## Cấu trúc và file nộp

```text
homework-buoi-6/
├── README.md
├── openapi.yaml
├── SecurityAudit.md
├── docs/
│   ├── authorization-matrix.md
│   └── test-scenarios.md
├── scripts/validate_openapi.py
├── requirements-dev.txt
└── .gitignore
```

Nộp toàn bộ tám file trên cùng commit chứa chúng; không nộp `.venv`, credential hoặc cache. Phần bắt buộc về nội dung là `openapi.yaml` và `SecurityAudit.md`; các file còn lại hỗ trợ giải thích/kiểm tra.

## Mở và kiểm tra OpenAPI

Từ thư mục buổi 6:

```bash
cd /home/tung/Desktop/SOA/api_session_06/homework-buoi-6
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_openapi.py
```

Mở [Swagger Editor](https://editor.swagger.io/), chọn File → Import file → `openapi.yaml`. Đây là tài liệu mẫu nên có thể nhập lên trình biên tập trực tuyến; không nhập token/password thật. `servers` dùng miền `.invalid` dành cho minh họa, **Try it out không có backend để gọi**.

Script parse YAML (từ chối key trùng), chạy `openapi-spec-validator` dành cho OpenAPI 3.0.3, resolve mọi `$ref` nội bộ, kiểm tra ví dụ bằng schema và format checker, kiểm tra ba operation/security/status/schema/header, số mục audit và các quy tắc chính. Dependency cài vào môi trường riêng và không được đưa vào Git. Kết quả validate tài liệu không chứng minh backend an toàn.

## Mô hình dữ liệu phục vụ thiết kế

| Khái niệm | Trường và quy tắc |
|---|---|
| User (nội bộ) | `id`: integer dương; `email`: duy nhất theo quy tắc chuẩn hóa nhất quán; `password_hash`: Argon2id có salt riêng, cấu hình chi phí theo đo tải; `roles`: `user`/`admin`; `status`: `active`/`locked`; `token_version`: integer tăng khi khóa tài khoản/đổi role/đổi password/thu hồi toàn bộ access token. Không trả hash ra API. |
| Post | `id`, `author_id`: integer dương; `content`: 1–10000 ký tự; `visibility`: `public`/`private`; `created_at`, `updated_at`: RFC3339 UTC. Response chỉ có các trường này. |
| Refresh family/session (nội bộ) | `family_id`, `user_id`, `created_at`, `expires_at` tuyệt đối, `revoked_at` nullable, `initial_scopes`; mỗi token có `token_hash`, `generation`, `used_at`, `replaced_by`. Lưu hash của token cũ đến hạn family để phát hiện reuse. `family_id`/generation là metadata, không gửi cho client. |

Refresh token là chuỗi opaque ngẫu nhiên từ CSPRNG với ít nhất 256 bit entropy, chỉ lưu hash (ví dụ SHA-256 vì token ngẫu nhiên mạnh, khác password). Không dùng UUID tuần tự hoặc dữ liệu do client cung cấp làm token. Những trường nội bộ không phải schema response; không có database hoặc migration trong bài này.

## Endpoint và quyền

| Endpoint | Credential | Scope có sẵn | Thành công | Lỗi hợp đồng |
|---|---|---|---|---|
| `POST /auth/login` | Email/password trong JSON | Không | 200 | 400, 401, 415, 429 |
| `POST /auth/refresh` | Refresh token trong JSON | Không cần access scope | 200 | 400, 401, 415, 429 |
| `GET /posts/{id}` | Bearer access JWT | `posts:read` | 200 | 400, 401, 403, 404, 429 |

Login/refresh khai báo `security: []` để không đòi security scheme ở header; server vẫn kiểm tra credential trong body. GET dùng `bearerAuth: []`, scope thể hiện bằng `x-required-scopes: [posts:read]` và description. Không khai báo OAuth2 password flow.

User/admin đang active được server cấp `posts:read`; client không chọn role/scope. GET kiểm authentication → scope → định dạng ID → tìm bài → ownership. Token hợp lệ nhưng thiếu scope trả 403 trước khi tra bài. Public cũng cần token và scope. Private chỉ tác giả hoặc admin hiện tại được đọc; admin cũng cần scope. Bài không tồn tại trả 404. Không phải owner/admin trả 403, chấp nhận khả năng lộ sự tồn tại của private post; muốn che bằng 404 phải đổi đồng bộ hợp đồng/checklist.

## Profile token và thu hồi

**Access token:** JWT ký RS256 bằng khóa do server quản lý, TTL thiết kế 900 giây (15 phút). Chỉ RS256 từ allowlist; từ chối `none`, HS256 hoặc thuật toán khác. Không tải khóa từ URL `jku/x5u` do token cung cấp; `kid` chỉ tra key registry tin cậy. Header `typ=JWT`; bắt buộc claims `sub` (chuỗi ID user), `iss=https://auth.social.example.invalid`, `aud=social-network-api`, `iat`, `nbf`, `exp`, `jti`, `token_use=access`, `token_version`, `scope`. Kiểm signature trước khi tin claims, kiểm đúng issuer/audience/type và định dạng claims; `nbf=iat`, `exp>iat`, `exp-iat<=900`, từ chối khi thời điểm hiện tại >= exp; chỉ cho iat/nbf lệch về tương lai tối đa 30 giây để dung sai đồng hồ. `expires_in` là giây còn lại tại thời điểm cấp. Không nhúng email, password, hash, secret hoặc nội dung bài vào JWT.

**Refresh token:** opaque, không phải JWT nên không có thuật toán ký/issuer/audience để kiểm như access JWT. Server kiểm hash, hạn, family, trạng thái tài khoản và ràng buộc chủ sở hữu từ kho phiên đáng tin cậy. Không nhận access JWT thay refresh, không nhận refresh để đọc bài. TTL family tuyệt đối 604800 giây (7 ngày) từ login, không trượt theo rotation; `refresh_expires_in` giảm theo thời gian còn lại. Hai TTL là lựa chọn bổ sung, không phải con số bắt buộc của đề.

**Rotation:** transaction hoặc compare-and-swap vừa tiêu thụ token hiện tại vừa lưu token kế tiếp. Thành công trả hai token mới, token cũ hết hiệu lực. Mỗi family độc lập cho một phiên thiết bị. Token cũ xuất hiện lại: trả 401 chung, thu hồi toàn bộ family và ghi audit event chỉ chứa ID nội bộ an toàn; không đưa chi tiết replay ra client. Hai request cùng token có tối đa một 200; request thua trả 401 và thu hồi family, nên refresh token vừa trả cho request thắng cũng bị thu hồi. Client phải tuần tự hóa refresh và đăng nhập lại sau replay; bài chọn chính sách nghiêm ngặt, không có grace window.

**Quyền hiện tại:** khi refresh, nạp lại role/scope từ server và lấy giao với `initial_scopes` của family để không tự mở rộng quyền. Nếu không còn `posts:read` hoặc tài khoản bị khóa, thu hồi family và trả 401 chung. Khi GET, ngoài kiểm chữ ký phải đọc trạng thái user và so `token_version` hiện tại; role admin dùng dữ liệu hiện tại của server. Khóa tài khoản, thay role/password hoặc yêu cầu thu hồi toàn bộ access token phải tăng version và thu hồi các refresh family liên quan trong cùng thay đổi nghiệp vụ. Thiết kế này hy sinh tính stateless hoàn toàn để chặn quyền cũ ngay, không dựa vào cache trạng thái có thể lỗi thời.

**Phân biệt thu hồi:** thu hồi một refresh family do replay không tự tăng user token_version và không tự hủy access token đã phát. Những access token đó có thể dùng đến hết tối đa 15 phút; nếu cần ứng phó sự cố tức thì phải chủ động tăng token_version (ảnh hưởng mọi access token của user) hoặc triển khai denylist `jti`. Bài không cung cấp endpoint logout/revoke ngoài ba endpoint được giao.

## Request/response và luồng sử dụng

1. Gửi `POST /auth/login`, `Content-Type: application/json` với email/password. Credential sai, user không tồn tại và tài khoản bị khóa cùng `401 invalid_credentials`; không phân biệt bằng message, cố gắng đồng nhất thời gian xử lý và áp dụng rate limit.
2. Đọc `access_token`, gọi `GET /posts/42` bằng `Authorization: Bearer <access_token>`. Kiểm authentication, scope và ownership độc lập.
3. Khi access token hết hạn, gửi refresh token tới `POST /auth/refresh` bằng JSON, không cần Authorization. Lưu thay thế cả cặp token sau 200 và bỏ token cũ. Không refresh lại đồng thời hoặc retry mù sau lỗi mạng vì có thể đã tiêu thụ token.

Ví dụ sau đều là dữ liệu minh họa không dùng được; không có tài khoản mẫu được tạo:

```http
POST /auth/login
Content-Type: application/json

{"email":"student@example.com","password":"DEMO_ONLY_NOT_A_REAL_PASSWORD"}
```

```json
{"access_token":"DEMO_ONLY_ACCESS_TOKEN_NOT_VALID","refresh_token":"DEMO_ONLY_REFRESH_TOKEN_NOT_VALID","token_type":"Bearer","expires_in":900,"refresh_expires_in":604800,"scope":"posts:read","user":{"id":1,"roles":["user"]}}
```

```http
GET /posts/42
Authorization: Bearer DEMO_ONLY_ACCESS_TOKEN_NOT_VALID
```

```http
POST /auth/refresh
Content-Type: application/json

{"refresh_token":"DEMO_ONLY_REFRESH_TOKEN_NOT_VALID"}
```

Ví dụ refresh 200 trong spec là sau 900 giây: token mới mang nhãn `DEMO_ONLY_NEW_...`, `refresh_expires_in=603900`. Ví dụ GET 200 chỉ có `id/author_id/content/visibility/created_at/updated_at` (xem spec), không chứa email/hash. Các request với DEMO_ONLY sẽ không xác thực được trên backend thật.

Lỗi dùng chung `{"error":{"code":"insufficient_scope","message":"Bạn không có quyền thực hiện thao tác này."}}`. JSON thiếu field, rỗng/sai kiểu, quá giới hạn hoặc field lạ trả 400; không nhận `roles`/`scope` từ client. Password dài 1–128 ký tự theo hợp đồng login; đây không phải chính sách đặt password lúc đăng ký. Không trim/cắt password. Refresh chuỗi không rỗng nhưng sai credential trả 401; thiếu/rỗng field trả 400. Sai Content-Type trả 415.

Token response bắt buộc `Cache-Control: no-store`, `Pragma: no-cache`; mọi response GET post kể cả lỗi có `Cache-Control: no-store`. Với GET 401 luôn có `WWW-Authenticate`: thiếu token dùng `Bearer realm="social-network"`, token sai thêm `error="invalid_token"`. GET 403 thiếu scope thêm `error="insufficient_scope", scope="posts:read"`; lỗi ownership không dùng challenge này. Login/refresh không dùng Bearer challenge vì nhận loại credential khác qua body. 429 có `Retry-After` số giây; rate limit theo IP và email/phiên/user tương ứng. Production bắt buộc HTTPS, không log credential, không lưu token trong URL. Lỗi hạ tầng bất ngờ phải được làm sạch; danh sách status tập trung vào các tình huống được giao, chưa thiết kế vận hành backend đầy đủ.

## Giải thích để trình bày

- **Authentication** xác định người gọi và kiểm credential/token. **Authorization** quyết định người đó được làm gì và với đối tượng nào.
- **Access token** dùng gọi API trong thời gian ngắn. **Refresh token** dùng xin cặp token mới, cần lưu trạng thái/rotation và không dùng đọc bài.
- **JWT** là định dạng token chứa claims, có thể ký để kiểm tra tính toàn vẹn. **OAuth2** là giao thức ủy quyền; dùng JWT/login riêng không có nghĩa đã triển khai OAuth2 hoặc OIDC.
- **Scope** là quyền hành động (`posts:read`), **role** là vai trò nghiệp vụ (`admin`), **ownership** là quan hệ với bản ghi (`author_id == user.id`). Cần kiểm cả scope lẫn đối tượng.
- Token hợp lệ vẫn nhận **403** khi thiếu scope hoặc không được đọc private post.
- JWT ký thông thường dùng Base64url để biểu diễn payload, không mã hóa bí mật. Người giữ token có thể đọc claims; chữ ký không che password/secret.

## Giới hạn và tình trạng kiểm tra

Kết quả kiểm tra tài liệu ngày 27/10/2026: YAML parse thành công, OpenAPIV30SpecValidator thành công, resolve 42 lượt `$ref`, 78 ví dụ hợp schema/format; các kiểm tra endpoint/security/status/header/rotation và 10 mục audit đều PASS. Rà mẫu secret phổ biến trong tám file bài tập không thấy kết quả; đây không phải quét toàn bộ Git history hoặc bằng chứng không thể có secret. Git không có thay đổi tracked/staged, chỉ tám file mới thuộc bài này; `.venv` đã được ignore.

Đã viết hợp đồng, audit thiết kế và checklist. Script có thể kiểm tra cấu trúc/ví dụ và ràng buộc tĩnh, không thực thi authentication, rotation, race condition, cache hoặc rate limit. Không có backend buổi 6, database, PDF, Postman collection hoặc kiểm thử runtime; 10 mục audit là rủi ro cần kiểm soát, không phải 10 lỗ hổng đã xác nhận trong mã nguồn. Xem [checklist](docs/test-scenarios.md) để kiểm thử khi triển khai.

## Git và nộp bài

Không tự commit/push. Sau khi xem lại, từ repository gốc chỉ stage tám file bài này:

```bash
cd /home/tung/Desktop/SOA
git status --short --branch
git add -- api_session_06/homework-buoi-6/README.md api_session_06/homework-buoi-6/openapi.yaml api_session_06/homework-buoi-6/SecurityAudit.md api_session_06/homework-buoi-6/docs/authorization-matrix.md api_session_06/homework-buoi-6/docs/test-scenarios.md api_session_06/homework-buoi-6/scripts/validate_openapi.py api_session_06/homework-buoi-6/requirements-dev.txt api_session_06/homework-buoi-6/.gitignore
git diff --cached --stat
git diff --cached --name-only
# Chỉ commit khi phần staged đã đúng phạm vi; không tự bỏ stage bài của người khác.
git commit -m "docs: add SOA session 6 auth OpenAPI spec and security audit"
git push origin main
git log -1 --oneline
```

`origin` đã có sẵn; lệnh push trên phù hợp nhánh `main` tại thời điểm kiểm tra. Nếu branch hoặc quy tắc repository thay đổi, dùng branch đã được nhóm chấp thuận. Không force push, sửa lịch sử, tạo remote hoặc tự thay branch. **Commit vẫn chờ bạn thực hiện hoặc xác nhận; bài chưa có commit để nộp cho đến bước đó.**

## Tham khảo chính thức

Không thay thế slide chưa có. Cách khai báo Bearer/security theo [OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3); kiểm JWT theo [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html); challenge tham khảo [RFC 6750 §3](https://www.rfc-editor.org/rfc/rfc6750.html#section-3). Ý tưởng giữ quan hệ refresh token để phát hiện reuse tham khảo [RFC 9700 §4.14](https://www.rfc-editor.org/rfc/rfc9700.html#section-4.14); chỉ áp dụng nguyên tắc bảo vệ, không tuyên bố hệ thống này triển khai OAuth2.

Lưu password tham khảo [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html); khi triển khai phải chọn tham số Argon2id cụ thể theo hướng dẫn và đo tải, bài này chỉ thiết kế hợp đồng.
