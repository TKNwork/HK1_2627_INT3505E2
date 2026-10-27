# Checklist kiểm thử dự kiến

**Tất cả tình huống bên dưới chưa chạy runtime.** Không có backend buổi 6. Chỉ script validate tài liệu được chạy riêng; các ví dụ DEMO_ONLY không thể dùng làm token trong test authentication. Khi triển khai cần fixture A/B/admin, public/private post, khóa thử và đồng hồ có kiểm soát; không dùng tài khoản production.

| Mã | Tình huống | Thiết lập/thao tác | Kỳ vọng | Trạng thái |
|---|---|---|---|---|
| TC-01 | Login hợp lệ | User thử active; email/password đúng | 200; đủ TokenResponse, không hash/email; no-store, no-cache. | Chưa chạy runtime |
| TC-02 | Không dò được email qua lỗi | Thử email không tồn tại, password sai, user khóa | Cùng 401 invalid_credentials và message; đo timing theo SA-02. | Chưa chạy runtime |
| TC-03 | Dữ liệu sai | Từng endpoint POST: JSON hỏng, thiếu field, null, kiểu số, chuỗi rỗng, vượt maxLength; GET ID abc/0/-1 với token hợp lệ | 400 invalid_request; không stack trace. | Chưa chạy runtime |
| TC-04 | Refresh hợp lệ | T0 đang active, sau login 900 giây, không gửi Authorization | 200, access mới + T1 mới, scope hiện tại, expires_in=900, refresh_expires_in≈603900 theo đồng hồ server; T0 đã dùng. | Chưa chạy runtime |
| TC-05 | Access token thay refresh | Gửi JWT access hợp lệ vào refresh_token | 401 invalid_refresh_token; không cấp token. | Chưa chạy runtime |
| TC-06 | Refresh hết hạn/thu hồi | Gửi token của family hết hạn 7 ngày hoặc revoked | 401 cùng message, không tiết lộ nguyên nhân nội bộ. | Chưa chạy runtime |
| TC-07 | Replay sau rotation | T0→T1 thành công; dùng lại T0 rồi dùng T1 | T0 401, family revoked, T1 401; audit event không chứa token. | Chưa chạy runtime |
| TC-08 | Refresh đồng thời | Barrier gửi hai request cùng T0, kiểm response và kho phiên | Tối đa một 200, request thua 401; family revoked nên token refresh mới cũng vô hiệu. Không có hai 200; client đăng nhập lại. | Chưa chạy runtime |
| TC-09 | Thiếu access token | GET public hoặc private mà không có Authorization | 401 unauthorized; WWW-Authenticate: Bearer realm="social-network". | Chưa chạy runtime |
| TC-10 | Access hết hạn/sai loại | GET với JWT exp cũ hoặc refresh token opaque | 401 invalid_token; WWW-Authenticate có error="invalid_token". | Chưa chạy runtime |
| TC-11 | Thiếu scope | JWT hợp lệ thiếu posts:read; thử cả user/admin | 403 insufficient_scope, challenge có scope="posts:read", không tra/lộ post trước scope. | Chưa chạy runtime |
| TC-12 | Owner đọc private | User A có scope đọc post private author_id=A.id | 200 đúng Post. | Chưa chạy runtime |
| TC-13 | Người khác đọc private | User A có scope đọc private của B | 403 forbidden; không chứa content và không có challenge insufficient_scope. | Chưa chạy runtime |
| TC-14 | Admin theo chính sách | Admin hiện tại có token/scope; thử thêm thiếu token, thiếu scope | Private B: 200; thiếu token 401; thiếu scope 403, không được bỏ qua. | Chưa chạy runtime |
| TC-15 | Post không tồn tại | Token/scope hợp lệ, ID integer dương không có trong DB | 404 post_not_found; không có query/stack trace. | Chưa chạy runtime |
| TC-16 | Không lộ dữ liệu | Kiểm mọi body token/post/error, JWT và header/cache | Đúng allowlist, không email/hash/secret/SQL/token trong lỗi; token no-store/no-cache, mọi GET response no-store. | Chưa chạy runtime |
| TC-17 | Chống client tự cấp quyền | Thêm roles/scope/user_id vào login hoặc refresh | 400 invalid_request do field không hỗ trợ, không cấp quyền. | Chưa chạy runtime |
| TC-18 | Content-Type sai | POST text/plain hoặc không gửi Content-Type JSON | 415 unsupported_media_type; không cố parse như JSON. | Chưa chạy runtime |
| TC-19 | Rate limiting | Vượt ngưỡng cấu hình riêng từng endpoint với user/IP/email/phiên thử | 429 rate_limit_exceeded và Retry-After >=1; không trả credential. | Chưa chạy runtime |
| TC-20 | JWT profile | Token none/HS256, chữ ký sai, thiếu sub/iat/nbf/exp/jti/token_use/version/scope, iss/aud sai, kid không tin cậy | 401; không tải key từ URL trong token; chi tiết không lộ ra body. | Chưa chạy runtime |
| TC-21 | Khóa/đổi quyền | Giữ cặp token, khóa user hoặc đổi role/password và tăng version, revoke family | GET token cũ 401; refresh cũ 401; role mới chỉ áp dụng sau xác thực/cấp mới đúng chính sách. | Chưa chạy runtime |
| TC-22 | Giới hạn revoke refresh | Access đang còn hạn; reuse refresh gây revoke family, không đổi version | Refresh tiếp theo 401; access có thể còn dùng đến exp (tối đa 900 giây). Tăng version chủ động mới chặn ngay. | Chưa chạy runtime |
| TC-23 | Hạn tuyệt đối family | Refresh nhiều lần đến sát mốc login+7 ngày | Không reset về 7 ngày; refresh_expires_in là thời gian còn lại; đến expires_at trả 401. | Chưa chạy runtime |
| TC-24 | Public có authentication | User không phải owner nhưng có token/scope đọc public của B | 200; anonymous vẫn 401. | Chưa chạy runtime |
| TC-25 | Logging/transport | Dùng credential thử có nhãn; kiểm proxy/app/audit logs và HTTPS | Không raw credential/Authorization/query token; HTTPS bắt buộc; chưa có hạ tầng để chạy. | Chưa chạy runtime |

Ưu tiên lỗi khi nhiều điều kiện cùng sai: có thể chặn rate limit trước xử lý; POST Content-Type sai trả 415 trước parse/credential, JSON/schema sai trả 400 trước xác thực. GET authentication → scope → ID → tìm bài → ownership. Khi đo rate limit/timing phải cô lập từng điều kiện để không hiểu nhầm 429 thành kết quả authentication. Race test phải kiểm cả transaction và trạng thái family sau khi hai request hoàn tất, không chỉ HTTP status.
