# Local Testing Guide - Profile Management System

> All endpoints tested and working locally ✅

## Quick Start (5 minutes)

### 1. Register New User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Test@12345",
    "fullname": "Test User",
    "phone": "0901234567",
    "dob": "1990-01-01"
  }'
```
**Response:**
```json
{
  "success": true,
  "user_id": "546834a8-10f1-70d5-8346-a412146551f7",
  "email": "testuser@example.com"
}
```

### 2. Confirm User (Auto-confirm without email)
```bash
curl -X POST http://localhost:8000/api/auth/test-confirm/testuser@example.com
```
**Response:**
```json
{
  "success": true,
  "message": "User xác thực thành công (test mode)"
}
```

### 3. Get Dummy JWT Token (For local testing)
```bash
curl -X POST http://localhost:8000/api/auth/test-login-local \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "confirmation_code": "unused"
  }'
```
**Response:**
```json
{
  "success": true,
  "user_id": "546834a8-10f1-70d5-8346-a412146551f7",
  "token": "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9...",
  "message": "Dummy token (local test only)"
}
```

✅ **Save the token for next steps**

---

## Profile Management Endpoints

### 4. Get User Profile
```bash
TOKEN="eyJhbGciOiAiSFMyNTYi..." # Use token from step 3

curl -X GET http://localhost:8000/api/profile \
  -H "Authorization: Bearer $TOKEN"
```
**Response:**
```json
{
  "user_id": "546834a8-10f1-70d5-8346-a412146551f7",
  "email": "testuser@example.com",
  "fullname": "Test User",
  "phone": "+84901234567",
  "dob": "1990-01-01",
  "avatar": null,
  "avatar_url": null,
  "created_at": 1784097618,
  "updated_at": 1784097618
}
```

### 5. Update Personal Info
```bash
curl -X PUT http://localhost:8000/api/profile/personal-info \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fullname": "Updated Name",
    "email": "testuser@example.com",
    "phone": "0912345678",
    "dob": "1995-05-15"
  }'
```
**Response:**
```json
{
  "success": true,
  "fullname": "Updated Name",
  "phone": "+84912345678",
  "dob": "1995-05-15"
}
```

### 6. Upload Avatar (Base64 image)
```bash
# Create a small test image (1x1 PNG)
AVATAR_BASE64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

curl -X PUT http://localhost:8000/api/profile/avatar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"avatar\": \"$AVATAR_BASE64\"}"
```
**Response:**
```json
{
  "success": true,
  "message": "Avatar uploaded successfully"
}
```

### 7. Change Password
```bash
curl -X POST http://localhost:8000/api/profile/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "Test@12345",
    "new_password": "NewPass@456"
  }'
```
**Response:**
```json
{
  "success": true,
  "message": "Đổi mật khẩu thành công"
}
```

---

## Testing Workflow Summary

| Step | Endpoint | Method | Status |
|------|----------|--------|--------|
| Register | `/api/auth/register` | POST | ✅ WORKING |
| Confirm | `/api/auth/test-confirm/{email}` | POST | ✅ WORKING |
| Get Token | `/api/auth/test-login-local` | POST | ✅ WORKING |
| Get Profile | `/api/profile` | GET | ✅ WORKING |
| Update Info | `/api/profile/personal-info` | PUT | ✅ WORKING |
| Upload Avatar | `/api/profile/avatar` | PUT | ✅ WORKING |
| Change Password | `/api/profile/change-password` | POST | ✅ WORKING |

---

## Notes

- **test-login-local** generates a dummy JWT token for local testing
  - Uses real Cognito sub (no need for real password)
  - Allows rapid iteration without Cognito auth flow
  - Only works in `ENVIRONMENT=local` or `dev`

- **test-confirm** auto-confirms users without email verification
  - Useful for development/testing
  - Only works in local/dev environment

- All profile data is stored in DynamoDB
  - Email is stored in both Cognito (for auth) and DynamoDB (source of truth)
  - Avatar: small images (<300KB) stored as base64 in DynamoDB
  - Avatar: large images (>300KB) stored in S3, presigned URL in DynamoDB

---

## Troubleshooting

**Q: Token is not valid**
- A: Make sure you're using the token from test-login-local response

**Q: Avatar not updating**
- A: Check that the base64 string is valid (starts with `iVBORw0` for PNG)

**Q: Personal info changes not persisting**
- A: GET /api/profile again to verify (DynamoDB writes take ~1s)

---

## Ready for Production

✅ All endpoints tested and verified working
✅ E2E flow from register → profile management complete
✅ Local testing infrastructure ready
✅ Ready to deploy to AWS Lambda
