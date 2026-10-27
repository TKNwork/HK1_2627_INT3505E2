
1: Lưu mật khẩu chưa an toàn

phần lưu user và POST /auth/login.
nếu lưu mật khẩu dạng chữ thường hoặc dùng hash nhanh, không có salt, thì khi database hay bản backup bị lấy mất, người khác sẽ dễ lấy được mật khẩu hơn.
Dữ liệu/quyền có thể lộ: mật khẩu và tài khoản người dùng. Mức độ và lý do: cao, vì nhiều người dùng lại một mật khẩu cho nhiều nơi, nên ảnh hưởng có thể vượt ra ngoài API này.

Giảm thiểu: dùng Argon2id với salt riêng cho từng mật khẩu, chọn chi phí hash phù hợp với máy chạy. Ngoài ra cần giới hạn người được đọc database và backup, không trả password_hash trong response.
Cách kiểm tra: tạo hai tài khoản thử có cùng mật khẩu rồi xem hash có khác nhau không, xem cấu hình hash đang dùng, sau đó thử đăng nhập đúng và sai mật khẩu.
2: Thử mật khẩu liên tục và dò email
POST /auth/login.
người tấn công có thể thử rất nhiều mật khẩu, hoặc dùng danh sách email/password bị lộ từ nơi khác. Nếu API báo “email không tồn tại” riêng với “sai mật khẩu” thì họ còn biết được email nào đã đăng ký. Thời gian trả lời khác nhau rõ rệt cũng có thể làm lộ thông tin này.
Dữ liệu/quyền có thể lộ: danh sách tài khoản và quyền đăng nhập nếu đoán đúng. Mức độ và lý do: cao, vì có thể thử tự động trên nhiều tài khoản.
Giảm thiểu: giới hạn số lần thử theo IP và email đã chuẩn hóa. Email không có, mật khẩu sai hoặc tài khoản bị khóa đều trả cùng lỗi 401 invalid_credentials. Với email không tồn tại vẫn nên thực hiện phép kiểm tra hash giả để giảm khác biệt thời gian; không khóa tài khoản vĩnh viễn chỉ vì có người nhập sai nhiều lần.
Ktra: so sánh code và message của cả ba trường hợp, đo thời gian qua nhiều lần gọi. Thử vượt ngưỡng để xem có trả 429 và Retry-After không, kể cả khi request đến từ nhiều IP.

3: Có JWT là cho qua, không kiểm tra kỹ

bước xác thực Bearer token ở GET /posts/{id}.
server chỉ giải mã JWT để đọc dữ liệu mà không kiểm chữ ký, hoặc tin luôn thuật toán và địa chỉ lấy khóa do token gửi lên. Bỏ qua hạn dùng hay issuer/audience cũng gây vấn đề tương tự.
Dữ liệu/quyền có thể lộ: người khác có thể giả danh user, thậm chí admin, để đọc bài riêng tư. Mức độ và lý do: nghiêm trọng vì có thể vượt qua bước xác thực.
Giảm thiểu: bài này chọn RS256, chỉ chấp nhận thuật toán đó và khóa do server quản lý. Cần kiểm chữ ký, exp, iat, nbf, iss, aud, sub, jti, token_use, token_version và scope theo profile trong README. Không tự tải khóa từ URL trong token và không nhận refresh token để đọc bài.
Cách kiểm tra: dùng token thử sai chữ ký, sai khóa, alg=none, HS256, sai issuer/audience, hết hạn hoặc thiếu claim bắt buộc. Các trường hợp này phải bị từ chối với 401 và WWW-Authenticate phù hợp.

4: Dùng lại refresh token cũ
POST /auth/refresh và phần lưu phiên refresh.
 refresh token bị sao chép rồi dùng lại, hoặc hai request cùng gửi một token trong lúc server chưa kịp đánh dấu token đã dùng. Nếu chỉ kiểm tra rồi cập nhật riêng từng bước thì cả hai request có thể cùng thành công.
Dữ liệu/quyền có thể lộ: khả năng xin access token mới để tiếp tục truy cập. Mức độ cao, vì hết hạn access token chưa chắc đã chặn được người đang giữ refresh token.

Giảm thiểu: dùng HTTPS, sinh refresh token ngẫu nhiên bằng CSPRNG với ít nhất 256 bit entropy và chỉ lưu hash. Mỗi lần refresh phải vừa đánh dấu token cũ đã dùng vừa lưu token mới trong cùng transaction hoặc compare-and-swap. Giữ lại hash token cũ để phát hiện dùng lại. Khi phát hiện thì thu hồi cả nhóm token của phiên, trả 401 chung. Hạn của nhóm là 7 ngày tính từ login, không cộng lại 7 ngày mỗi lần refresh.
Cách kiểm tra: đổi T0 lấy T1, sau đó gửi lại T0 thì phải nhận 401 và T1 cũng không refresh được nữa. Gửi hai request cùng T0 phải có tối đa một request nhận 200; request còn lại 401 và làm phiên bị thu hồi, kể cả refresh token vừa cấp. Cần kiểm riêng access token vì thu hồi refresh không tự làm access JWT mất hiệu lực.

5: Quên kiểm tra scope

GET /posts/{id}.
server chỉ kiểm token hợp lệ rồi trả bài viết, hoặc cho rằng admin thì không cần kiểm scope nữa.
Dữ liệu/quyền có thể lộ: bài viết có thể bị đọc bởi tài khoản không có quyền posts:read. Mức độ và lý do: cao vì bước kiểm tra quyền hành động bị bỏ qua.
Giảm thiểu: sau xác thực phải kiểm posts:read trước khi tìm bài viết, áp dụng với cả user và admin. Trong OpenAPI, Bearer dùng danh sách rỗng []; scope được ghi ở description và x-required-scopes.
Cách kiểm tra: cấp token thử hợp lệ nhưng thiếu posts:read cho cả user và admin. Kết quả phải là 403 insufficient_scope, có WWW-Authenticate nêu scope cần thiết.


