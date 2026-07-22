# EVENTBRIDGE SETUP GUIDE - Auto Cleanup Unconfirmed Users

Hướng dẫn này mô tả cách thiết lập **Amazon EventBridge Scheduled Rule** để tự động xóa các Cognito users ở trạng thái `UNCONFIRMED` sau 5 phút.

---

## 📋 TẠI SAO CẦN FEATURE NÀY?

### Vấn đề

Khi user đăng ký tài khoản nhưng **không xác thực email**, Cognito vẫn giữ user record ở trạng thái `UNCONFIRMED`:
- Chiếm slot trong User Pool (Cognito có giới hạn 40M users/pool, nhưng best practice là cleanup)
- Không thể đăng ký lại cùng email (vì Cognito xem như email đã tồn tại)
- Gây confuse: user quên verify, thử đăng ký lại → báo lỗi "Email already exists"

### Giải pháp

**Tự động xóa** user `UNCONFIRMED` sau **5 phút** bằng EventBridge Scheduled Rule.

### Architecture

```
EventBridge Rule (rate: 1 minute)
    ↓
Lambda: smartdocai (handler function)
    ↓
Check event.source == "aws.events"?
    ├─ YES → auth_service.cleanup_unconfirmed_users()
    │         ↓
    │         Cognito: list_users(Filter='cognito:user_status = "UNCONFIRMED"')
    │         ↓
    │         Loop each user → check UserCreateDate > 5 mins?
    │         ↓
    │         admin_delete_user()
    │
    └─ NO → Mangum (process as HTTP request)
```

---

## 🚀 HƯỚNG DẪN TRIỂN KHAI

### Bước 1: Verify Code đã có sẵn

**✅ Code đã có trong source code:**

1. **Handler phân nhánh** trong `backend/app_api.py`:
   ```python
   def handler(event, context):
       if isinstance(event, dict) and event.get("source") == "aws.events":
           from modules.auth_service import cleanup_unconfirmed_users
           return cleanup_unconfirmed_users(max_age_minutes=5)
       return _mangum_handler(event, context)
   ```

2. **Function cleanup** trong `backend/modules/auth_service.py`:
   ```python
   def cleanup_unconfirmed_users(max_age_minutes: int = 5) -> dict:
       # List users with status UNCONFIRMED
       # Compare UserCreateDate with current time
       # Delete if age > max_age_minutes
   ```

**✅ Không cần sửa code, chỉ cần setup AWS infrastructure.**

---

### Bước 2: Tạo EventBridge Rule

#### Option A: AWS Console (Khuyến nghị cho lần đầu)

1. **Mở AWS Console** → **Amazon EventBridge** → **Rules**
2. Click **Create rule**
3. Nhập thông tin:

   | Field | Value |
   |---|---|
   | **Name** | `smartdocai-cleanup-unconfirmed-users` |
   | **Description** | Auto cleanup Cognito unconfirmed users after 5 minutes |
   | **Event bus** | `default` |
   | **Rule type** | Schedule |
   | **Schedule pattern** | Rate-based schedule |
   | **Rate expression** | `1` minute(s) |

4. Click **Next** → **Select target(s)**
5. Target configuration:

   | Field | Value |
   |---|---|
   | **Target type** | AWS service |
   | **Select a target** | Lambda function |
   | **Function** | `smartdocai` |
   | **Retry attempts** | 2 |
   | **Maximum age of event** | 1 hour |

6. Click **Next** → **Next** → **Create rule**

#### Option B: AWS CLI

```powershell
# 1. Tạo EventBridge Rule
aws events put-rule `
  --name smartdocai-cleanup-unconfirmed-users `
  --description "Auto cleanup Cognito unconfirmed users after 5 minutes" `
  --schedule-expression "rate(1 minute)" `
  --region us-east-1

# 2. Add Lambda permission cho EventBridge
aws lambda add-permission `
  --function-name smartdocai `
  --statement-id EventBridgeInvokeCleanup `
  --action lambda:InvokeFunction `
  --principal events.amazonaws.com `
  --source-arn arn:aws:events:us-east-1:623035187993:rule/smartdocai-cleanup-unconfirmed-users `
  --region us-east-1

# 3. Add target (Lambda function) vào rule
aws events put-targets `
  --rule smartdocai-cleanup-unconfirmed-users `
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:623035187993:function:smartdocai" `
  --region us-east-1
```

**Lưu ý:** Thay `623035187993` bằng AWS Account ID của bạn (lấy từ `aws sts get-caller-identity`).

---

### Bước 3: Verify Setup

#### 3.1. Check Rule đã hoạt động chưa

```powershell
# Kiểm tra rule đã được tạo
aws events describe-rule --name smartdocai-cleanup-unconfirmed-users --region us-east-1

# Kiểm tra targets
aws events list-targets-by-rule --rule smartdocai-cleanup-unconfirmed-users --region us-east-1
```

**Expected output:**
```json
{
  "Name": "smartdocai-cleanup-unconfirmed-users",
  "Arn": "arn:aws:events:us-east-1:...",
  "State": "ENABLED",
  "ScheduleExpression": "rate(1 minute)"
}
```

#### 3.2. Check CloudWatch Logs

EventBridge sẽ invoke Lambda **mỗi 1 phút**, ngay cả khi không có user nào cần xóa.

1. AWS Console → **CloudWatch** → **Log groups** → `/aws/lambda/smartdocai`
2. Tìm log entries có pattern:
   ```
   [EventBridge] Nhận scheduled event, chạy cleanup unconfirmed users...
   [Cleanup] Quét 0 user UNCONFIRMED, xóa 0 user quá hạn
   ```

**Nếu thấy log này mỗi 1-2 phút → EventBridge đã hoạt động! ✅**

#### 3.3. Test với User thật

1. **Tạo test user** (KHÔNG verify email):
   ```powershell
   aws cognito-idp sign-up `
     --client-id 63f74h4dj78kqihhoimv4acl8a `
     --username test-cleanup@example.com `
     --password Test123! `
     --user-attributes Name=email,Value=test-cleanup@example.com `
     --region us-east-1
   ```

2. **Kiểm tra user tồn tại** (trạng thái `UNCONFIRMED`):
   ```powershell
   aws cognito-idp list-users `
     --user-pool-id us-east-1_3oq5wIiuu `
     --filter "email = \"test-cleanup@example.com\"" `
     --region us-east-1
   ```

3. **Đợi 6 phút** (> 5 minutes threshold)

4. **Kiểm tra lại** → User đã bị xóa:
   ```powershell
   aws cognito-idp list-users `
     --user-pool-id us-east-1_3oq5wIiuu `
     --filter "email = \"test-cleanup@example.com\"" `
     --region us-east-1
   ```
   
   **Expected:** `"Users": []` (empty)

5. **Check CloudWatch Logs** → sẽ thấy:
   ```
   [Cleanup] Xóa user: test-cleanup@example.com (đã tồn tại 6.2 phút)
   [Cleanup] Quét 1 user UNCONFIRMED, xóa 1 user quá hạn
   ```

---

## 📊 MONITORING

### CloudWatch Metrics (Custom - Optional)

Nếu muốn track số lượng users bị cleanup, thêm vào `auth_service.py`:

```python
import boto3
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

# Trong cleanup_unconfirmed_users():
cloudwatch.put_metric_data(
    Namespace='SmartDocAI',
    MetricData=[{
        'MetricName': 'UnconfirmedUsersDeleted',
        'Value': deleted_count,
        'Unit': 'Count'
    }]
)
```

Sau đó tạo CloudWatch Dashboard hoặc Alarm:
- Alert nếu `UnconfirmedUsersDeleted > 10` trong 1 giờ (có thể bị abuse)

---

## 💰 CHI PHÍ

| Resource | Usage | Cost |
|---|---|---|
| EventBridge rule | 1 invocation/minute = 43,200/month | **$0** (1M events/month Free Tier) |
| Lambda invocations | 43,200/month | **$0** (1M requests/month Free Tier) |
| Lambda duration | ~100ms/invocation = 4,320 seconds/month | **$0.00007** (GB-seconds) |
| Cognito Admin API | `list_users` + `admin_delete_user` | **$0** (Admin API không tính vào MAU) |
| CloudWatch Logs | ~1 KB/invocation = 40 MB/month | **$0** (5 GB ingestion/month Free Tier) |

**Tổng chi phí:** ~**$0/month** (nằm trong Free Tier)

---

## 🛠️ TROUBLESHOOTING

### Issue 1: Lambda không được invoke

**Triệu chứng:** CloudWatch Logs không có log từ EventBridge sau 2-3 phút.

**Nguyên nhân:**
- Lambda chưa có permission cho EventBridge invoke
- Rule chưa enable hoặc target chưa được thêm

**Fix:**
```powershell
# Check rule state
aws events describe-rule --name smartdocai-cleanup-unconfirmed-users

# Nếu State = "DISABLED" → enable:
aws events enable-rule --name smartdocai-cleanup-unconfirmed-users

# Check Lambda permission
aws lambda get-policy --function-name smartdocai --region us-east-1 | jq
# Phải thấy "Principal": "events.amazonaws.com"
```

### Issue 2: User không bị xóa dù đã > 5 phút

**Triệu chứng:** User vẫn `UNCONFIRMED` sau 10 phút.

**Debug steps:**
1. Check CloudWatch Logs → tìm `[Cleanup]` → có log không?
2. Nếu có log nhưng `deleted_count = 0`:
   - Verify `UserCreateDate` bằng CLI:
     ```powershell
     aws cognito-idp admin-get-user `
       --user-pool-id us-east-1_3oq5wIiuu `
       --username test-cleanup@example.com
     ```
   - Check `UserCreateDate` có > 5 minutes so với `now()` không?
3. Nếu không có log `[Cleanup]` → Lambda không nhận EventBridge event:
   - Check handler function trong `app_api.py` có logic `event.get("source") == "aws.events"`?

### Issue 3: Lambda timeout khi cleanup nhiều users

**Triệu chứng:** Task timed out after 3.00 seconds (nếu có hàng nghìn unconfirmed users).

**Fix:**
```powershell
# Tăng Lambda timeout lên 60 seconds
aws lambda update-function-configuration `
  --function-name smartdocai `
  --timeout 60 `
  --region us-east-1
```

Hoặc thêm pagination trong `cleanup_unconfirmed_users()`:
```python
# Chỉ xóa max 100 users mỗi lần chạy
for user in users[:100]:
    delete_user(user)
```

---

## 🔄 UPDATE/MODIFY SCHEDULE

### Đổi schedule từ 1 minute sang 5 minutes

```powershell
aws events put-rule `
  --name smartdocai-cleanup-unconfirmed-users `
  --schedule-expression "rate(5 minutes)" `
  --region us-east-1
```

### Đổi threshold từ 5 phút sang 10 phút

Sửa code trong `backend/app_api.py`:
```python
return cleanup_unconfirmed_users(max_age_minutes=10)  # Thay đổi từ 5 → 10
```

Sau đó deploy lại Lambda (push to GitHub → CodePipeline auto-deploy).

---

## 🗑️ XÓA EVENTBRIDGE RULE (Cleanup)

Nếu không cần feature này nữa:

```powershell
# 1. Remove targets
aws events remove-targets `
  --rule smartdocai-cleanup-unconfirmed-users `
  --ids "1" `
  --region us-east-1

# 2. Delete rule
aws events delete-rule `
  --name smartdocai-cleanup-unconfirmed-users `
  --region us-east-1

# 3. Remove Lambda permission (optional, không ảnh hưởng)
aws lambda remove-permission `
  --function-name smartdocai `
  --statement-id EventBridgeInvokeCleanup `
  --region us-east-1
```

---

## 📚 REFERENCES

- [Amazon EventBridge Schedule-based Rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)
- [Cognito Admin API - list_users](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ListUsers.html)
- [Lambda IAM Permissions for EventBridge](https://docs.aws.amazon.com/lambda/latest/dg/services-eventbridge.html)

---

**Cập nhật lần cuối:** 2026-07-22
**Status:** ✅ Đã có code, cần setup EventBridge Rule trên AWS
