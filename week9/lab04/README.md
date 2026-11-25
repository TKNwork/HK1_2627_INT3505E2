# Lab 04 · Blue-Green Routing

Chạy từ thư mục `week9` bằng PowerShell. Mặc định, 5% bucket tài khoản thông thường vào v2. Cohort `beta` hoặc `internal` và allow-list `acct_42`, `acct_99` được ưu tiên vào v2.

```powershell
$env:LAB04_V2_PERCENT = '5'
python -m flask --app lab04.app run
```

Ở terminal thứ hai, chạy các request và xem cột `Handler`, lấy từ response header `X-Order-Handler`.

```powershell
function Test-Order($account, $cohort) {
    $headers = @{}
    if ($cohort) { $headers['X-Cohort'] = $cohort }
    $body = @{ account_id = $account } | ConvertTo-Json -Compress
    $response = Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:5000/orders' `
        -Headers $headers -ContentType 'application/json' -Body $body
    [pscustomobject]@{
        Account = $account
        Cohort = $cohort
        Status = [int]$response.StatusCode
        Handler = $response.Headers['X-Order-Handler'] -join ', '
    }
}

Test-Order 'acct_1' 'beta'
Test-Order 'acct_42'
Test-Order 'acct_72'
Test-Order 'acct_21'
Test-Order 'acct_1'
```

| Rollout | Request | Kết quả đã kiểm tra |
| --- | --- | --- |
| 5% | `acct_1`, cohort `beta` | `201`, v2 |
| 5% | `acct_42`, trong allow-list | `201`, v2 |
| 5% | `acct_72`, bucket 3 | `201`, v2 |
| 5% | `acct_21`, bucket 5 | `200`, v1 |
| 5% | `acct_1`, bucket 53 | `200`, v1 |
| 100% | `acct_1`, bucket 53 | `201`, v2 |

Để kiểm tra bước chuyển lên 100%, dừng Flask, đặt `$env:LAB04_V2_PERCENT = '100'`, chạy lại Flask rồi gọi `Test-Order 'acct_1'`. Kiểm thử tự động với 1.000 request phủ đủ 100 bucket ở mức 100% xác nhận handler v1 nhận 0 lượt gọi.

Khi triển khai thực tế, giữ v1 trong 30 ngày sau khi đạt 100% ổn định để có thể hạ tỷ lệ nếu cần. Kiểm tra log và tỷ lệ lỗi trước khi lưu trữ v1. Mức 0% tắt rollout theo bucket, còn cohort và allow-list vẫn vào v2.
