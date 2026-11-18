# Lab 04 — Phân tích kết quả Locust

1. C có p95 cao nhất so với A và B. Tăng nhanh lên 200 user làm nhiều req chờ xử lý cùng lúc, độ trễ tăng khi tải tăng
2. Post tăng từ 0/29 lên 11/193 (B) và 53/198 (C), các lỗi post là http 500 từ flask. 
    B ghi nhận 11 lỗi 500 mà 1 lỗi giả lập, với C là 69 và 3. Phát sinh ở task search_by_year khi locust đánh dấu res 200 thất bại
3.Cả ba kịch bản đều đạt ngưỡng p95 < 300 ms. C có 2.58% lỗi --> có thể dùng A làm baseline cho CI

*
nếu chỉ có 5 connection, req cần truy cập DB để chờ lấy hoặc bị timeout. 
--> Test dùng BE có pool cấu hình được và chạy lại C với 2 pool. chú ý giữ nguyên dữ liệu và thông số tải. chỉ so sánh p95, rps và số lỗi timeout