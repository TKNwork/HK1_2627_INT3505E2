# Ma trận quyền

Đây là hợp đồng thiết kế, chưa kiểm thử backend.

| Endpoint | Credential | Scope | Quyền đối tượng | Thành công | Lỗi chính |
|---|---|---|---|---|---|
| POST /auth/login | Email/password JSON | Không yêu cầu trước login | Không áp dụng; tài khoản active | 200 | 400, 401, 415, 429 |
| POST /auth/refresh | Refresh token opaque trong body | Không cần access scope | Phiên, family, tài khoản và quyền hiện tại | 200 | 400, 401, 415, 429 |
| GET /posts/{id} | Bearer access JWT | posts:read | Visibility, owner hoặc admin | 200 | 400, 401, 403, 404, 429 |

| Trạng thái khi GET | Public tồn tại | Private của mình | Private người khác | ID không tồn tại |
|---|---|---|---|---|
| Thiếu/sai/hết hạn/sai loại token; tài khoản khóa hoặc version cũ | 401 | 401 | 401 | 401 |
| Token hợp lệ thiếu posts:read, kể cả admin | 403 insufficient_scope | 403 insufficient_scope | 403 insufficient_scope | 403 insufficient_scope |
| User hợp lệ, có posts:read | 200 | 200 | 403 forbidden | 404 |
| Admin hiện tại, token hợp lệ, có posts:read | 200 | 200 | 200 | 404 |

ID integer dương thống nhất. Sau authentication/scope, ID sai định dạng trả 400. Không dựa vào ID hoặc role từ request để nhận diện owner/admin. Public không có nghĩa anonymous được đọc. Trả 403 cho private post có thể tiết lộ sự tồn tại; đây là trade-off được chọn. GET cả thành công và lỗi dùng no-store.

Refresh 200 cấp cặp mới và tiêu thụ token cũ nguyên tử. Reuse trả 401 chung và thu hồi family, không tự hủy access JWT; access vẫn phải qua kiểm trạng thái/version khi GET. Khóa hoặc thay role/password tăng version và thu hồi phiên liên quan. `refresh_expires_in` giảm đến hạn tuyệt đối 7 ngày, không reset mỗi lần rotation. Xem README để biết profile và giới hạn thu hồi.
