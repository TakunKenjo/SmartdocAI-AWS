# SECURITY CONSIDERATIONS

Tài liệu này mô tả các biện pháp bảo mật hiện tại của SmartDocAI và các giới hạn cần cải thiện cho môi trường production.

> **Lưu ý:** Đây là hệ thống demo/thực tập. Một số security features chưa được triển khai do giới hạn thời gian và chi phí.

---

## ✅ CÁC BIỆN PHÁP BẢO MẬT HIỆN TẠI

### 1. Authentication & Authorization

**✅ Đã triển khai:**
- **AWS Cognito User Pool** cho identity management
- **JWT-based authentication** với RS256 signature verification
- **Multi-provider support:** Email/Password + Google OAuth 2.0
- **PreSignUp Lambda trigger** để merge duplicate accounts (AdminLinkProviderForUser)
- **Email verification** bắt buộc cho tất cả accounts
- **Password policy:** 
  - Tối thiểu 8 ký tự
  - Phải có chữ hoa, chữ thường, số
  - Managed bởi Cognito (hash với bcrypt)

**✅ Token management:**
- ID token expiry: 1 hour (configurable in Cognito)
- Refresh token: 30 days
- Backend verify JWT signature với PyJWT + Cognito public keys

### 2. Data Isolation

**✅ Đã triển khai:**
- **Per-user S3 prefixes:** `uploads/{user_id}/`, `vectorstore/{user_id}/`
- **DynamoDB partition key:** `user_id` (Cognito `sub`)
- **FAISS vector stores:** mỗi user có index riêng biệt
- **Chat history:** `chat_history/{user_id}.json` (không share giữa users)

**✅ Authorization logic:**
- Backend trích xuất `user_id` từ JWT claim `sub`
- Mọi file/data access phải có `user_id` trong path
- Không có cross-user queries

### 3. Input Validation & Sanitization

**✅ Đã triển khai:**
- **Fullname:** strip HTML tags, giới hạn 100 ký tự
- **Email:** validate format với regex
- **Phone:** E.164 format validation (regex + length check)
- **Date of birth:** ISO 8601 format (YYYY-MM-DD)
- **File upload:** 
  - Whitelist extensions: `.pdf`, `.docx` only
  - Mime type verification (though not comprehensive)
  - Max file size: 5 GB (S3 limit)
- **Avatar:** Base64 decode validation, size limit 300 KB inline / unlimited S3

### 4. Infrastructure Security

**✅ Đã triển khai:**
- **HTTPS only:** CloudFront + API Gateway enforce TLS 1.2+
- **IAM least privilege:** Lambda role chỉ có quyền cần thiết (S3, DynamoDB, Bedrock, Cognito)
- **VPC endpoints:** (Chưa triển khai, nhưng có thể thêm cho S3/DynamoDB)
- **Secrets management:** Credentials không hard-code, dùng environment variables
- **Container security:** Docker image scan với ECR (basic)
- **CORS restriction:** Chỉ allow CloudFront domain + localhost (dev)

### 5. Logging & Monitoring

**✅ Đã triển khai:**
- **CloudWatch Logs:** tất cả Lambda execution logs
- **Structured logging:** mỗi request có `user_id` trong log context
- **Error tracking:** exceptions được log với stack trace

---

## ⚠️ GIỚI HẠN BẢO MẬT HIỆN TẠI

### 1. Rate Limiting & DDoS Protection

**❌ CHƯA TRIỂN KHAI:**
- Không có rate limiting trên `/api/auth/register`, `/api/auth/login`
- Không có AWS WAF rules
- Dễ bị brute-force attacks

**💡 Khuyến nghị production:**
```yaml
# AWS WAF Rule cho rate limiting
- Rule: RateLimitAuthEndpoints
  RateLimit: 100 requests per 5 minutes per IP
  Action: Block
  Scope: /api/auth/*
  
- Rule: RateLimitAPIGeneral
  RateLimit: 1000 requests per 5 minutes per IP
  Action: Block
  Scope: /api/*
```

**Chi phí ước tính:** ~$5-10/month (WAF base + rules)

### 2. CORS Configuration

**⚠️ CẢI THIỆN GẦN ĐÂY:**
- ~~Trước đây: `AllowedOrigins: ["*"]` (quá rộng)~~ ✅ **ĐÃ SỬA**
- **Hiện tại:** Chỉ allow CloudFront domain + localhost (dev)

**✅ Đã update trong commit này.**

### 3. Audit Trail & Compliance

**❌ CHƯA TRIỂN KHAI:**
- Không track failed login attempts
- Không có alert cho suspicious activities (nhiều failed logins liên tiếp)
- CloudTrail enable nhưng chưa filter critical events

**💡 Khuyến nghị production:**
```python
# Thêm DynamoDB table: auth_audit_log
{
  "user_id": "xxx",
  "event_type": "LOGIN_FAILED",
  "ip_address": "1.2.3.4",
  "timestamp": 1234567890,
  "metadata": {"reason": "wrong_password"}
}

# Lambda thêm logic:
if failed_login_count_last_15min > 5:
    send_alert_to_sns()
    temporarily_lock_account()
```

**Chi phí ước tính:** ~$1-2/month (DynamoDB on-demand + SNS)

### 4. File Upload Security

**⚠️ CÓ BASIC, CẦN TĂNG CƯỜNG:**
- Mime type check không đủ (có thể fake headers)
- Không scan malware (ClamAV, VirusTotal)
- Không giới hạn số file per user (có thể abuse storage)

**💡 Khuyến nghị production:**
- S3 Event Notification → Lambda scan với ClamAV (open source) hoặc AWS GuardDuty Malware Protection ($0.50 per GB scanned)
- Thêm quota: max 100 files per user, max 1 GB total per user

### 5. Secrets Rotation

**❌ CHƯA TRIỂN KHAI:**
- Cognito Client Secret không rotate (hiện tại dùng public client nên không có secret)
- AWS credentials hardcode trong CodeBuild environment (không dùng Secrets Manager)
- Google OAuth credentials trong Cognito console (manual)

**💡 Khuyến nghị production:**
- Dùng AWS Secrets Manager với auto-rotation
- Store Google OAuth client secret trong Secrets Manager
- Chi phí: ~$0.40/secret/month + $0.05 per 10,000 API calls

### 6. SQL Injection & NoSQL Injection

**✅ AN TOÀN (ở mức hiện tại):**
- DynamoDB queries dùng boto3 parameterized (không có raw query)
- Không có SQL database nên không có SQL injection risk

**⚠️ Chú ý nếu mở rộng:**
- Nếu thêm RDS/Aurora → phải dùng ORM hoặc parameterized queries
- FAISS vector search: input đã được encode thành embeddings (không có injection risk)

### 7. CSRF Protection

**❌ CHƯA TRIỂN KHAI:**
- API là stateless (JWT-based), không có CSRF token
- Nếu browser cache JWT trong cookie → dễ bị CSRF

**✅ HIỆN TẠI AN TOÀN VÌ:**
- Frontend lưu JWT trong `sessionStorage` (không phải cookie)
- Browser không tự động gửi `sessionStorage` trong cross-origin requests

**💡 Khuyến nghị nếu chuyển sang cookie-based auth:**
- Thêm CSRF token với library như `itsdangerous` (Python)
- SameSite=Strict attribute cho cookies

### 8. API Response Information Disclosure

**⚠️ CẦN REVIEW:**
- Error messages có thể leak thông tin nhạy cảm (stack traces trong dev mode)
- Ví dụ: `UserNotFoundException` → attacker biết email không tồn tại

**💡 Đã có mitigation partial:**
- `/api/auth/resolve-login-username` giúp user không bị confuse, nhưng cũng leak info
- Production nên trả generic error: "Invalid credentials" thay vì specific reasons

### 9. Dependency Vulnerabilities

**⚠️ CẦN AUTOMATED SCANNING:**
- `requirements.txt` có 30+ dependencies, chưa scan CVEs thường xuyên
- Docker base image `python:3.11-slim` cần update định kỳ

**💡 Khuyến nghị:**
```yaml
# Thêm vào buildspec.yml
- pip install safety
- safety check --json
- docker scan $IMAGE_REPO_NAME:$IMAGE_TAG
```

### 10. Least Privilege IAM

**✅ TỐT (nhưng có thể tối ưu hơn):**
- Lambda role có `S3FullAccess`, `BedrockFullAccess` → nên restrict theo resource ARN

**💡 Khuyến nghị:**
```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::smartdocai-storage-*/uploads/*"
}
// Thay vì S3FullAccess
```

---

## 🛡️ SECURITY CHECKLIST CHO PRODUCTION

### High Priority (Phải có trước khi public)
- [ ] Triển khai AWS WAF với rate limiting
- [ ] Setup failed login attempt tracking + account lockout
- [ ] Scan dependencies với `safety` / `Dependabot`
- [ ] Restrict IAM policies theo least privilege (resource-level)
- [ ] Enable GuardDuty hoặc ClamAV malware scanning cho uploads
- [ ] Setup CloudWatch Alarms cho suspicious activities

### Medium Priority (Trong 1-2 tháng đầu)
- [ ] Implement audit logging vào DynamoDB
- [ ] Secrets rotation với AWS Secrets Manager
- [ ] Add file quota per user (prevent storage abuse)
- [ ] Setup automated security testing trong CI/CD (SAST tools)
- [ ] Review error messages (không leak info)

### Nice to Have (Long-term)
- [ ] VPC endpoints cho S3/DynamoDB (giảm latency + tăng security)
- [ ] AWS Security Hub integration
- [ ] Penetration testing bởi third-party
- [ ] SOC 2 compliance preparation

---

## 📚 REFERENCES

- [AWS Security Best Practices](https://docs.aws.amazon.com/security/latest/userguide/best-practices.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS WAF Pricing](https://aws.amazon.com/waf/pricing/)
- [Cognito Security Best Practices](https://docs.aws.amazon.com/cognito/latest/developerguide/security-best-practices.html)

---

**Cập nhật lần cuối:** 2026-07-22
