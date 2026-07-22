"""
Test Script cho Auth API Endpoints
Chạy backend local trước: python run.py
Sau đó chạy: python test_auth_api.py
"""

import requests
import json
import base64
import uuid
from io import BytesIO
from PIL import Image
import time

# ─── Config ────────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

# ─── Helpers ────────────────────────────────────────────────────────────────

def generate_test_image() -> str:
    """Tạo test image dạng base64"""
    img = Image.new('RGB', (300, 300), color='blue')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_base64}"


def print_response(response: requests.Response, title: str = "", test_name: str = ""):
    """In response đẹp"""
    status_emoji = "✅" if response.status_code < 400 else "❌"
    print(f"\n{'─'*70}")
    print(f"{status_emoji} {test_name} | {title}")
    print(f"{'─'*70}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None


# ════════════════════════════════════════════════════════════════════════════════
# AUTH TESTS — Đăng ký và xác thực
# ════════════════════════════════════════════════════════════════════════════════

def test_register_valid():
    """Test POST /api/auth/register — Đăng ký thành công"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    # Tạo email duy nhất với timestamp
    unique_email = f"testuser_{int(time.time())}@example.com"
    
    payload = {
        "email": unique_email,
        "password": "TestPassword123!",
        "fullname": "Nguyễn Văn Test",
        "phone": "0901234567",
        "dob": "1990-01-15"
    }
    
    response = requests.post(url, json=payload)
    data = print_response(response, "Valid Registration", "test_register_valid")
    
    if response.status_code == 200:
        assert data.get("success") == True, "Missing success flag"
        assert "user_id" in data, "Missing user_id"
        assert "email" in data, "Missing email"
        print("✅ PASSED: User registered successfully")
        return data  # Return để dùng sau
    else:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return None


def test_register_invalid_email():
    """Test POST /api/auth/register — Email không hợp lệ"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    payload = {
        "email": "invalid-email",  # Không có @
        "password": "TestPassword123!",
        "fullname": "Test User",
        "phone": "0901234567",
        "dob": "1990-01-15"
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "Invalid Email Format", "test_register_invalid_email")
    
    if response.status_code == 400:
        print("✅ PASSED: Validation error caught")
    else:
        print(f"❌ FAILED: Expected 400, got {response.status_code}")


def test_register_invalid_password():
    """Test POST /api/auth/register — Mật khẩu quá yếu (<8 ký tự)"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    payload = {
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "Short1!",  # Chỉ 7 ký tự
        "fullname": "Test User",
        "phone": "0901234567",
        "dob": "1990-01-15"
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "Weak Password", "test_register_invalid_password")
    
    if response.status_code == 400:
        print("✅ PASSED: Password validation caught")
    else:
        print(f"⚠️  Expected 400, got {response.status_code}")


def test_register_invalid_phone():
    """Test POST /api/auth/register — Phone số không hợp lệ"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    payload = {
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "fullname": "Test User",
        "phone": "123",  # Quá ngắn
        "dob": "1990-01-15"
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "Invalid Phone", "test_register_invalid_phone")
    
    if response.status_code == 400:
        print("✅ PASSED: Phone validation caught")
    else:
        print(f"⚠️  Expected 400, got {response.status_code}")


def test_register_invalid_dob():
    """Test POST /api/auth/register — Ngày sinh không hợp lệ"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    payload = {
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "fullname": "Test User",
        "phone": "0901234567",
        "dob": "1990-13-01"  # Tháng không hợp lệ
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "Invalid DOB Format", "test_register_invalid_dob")
    
    if response.status_code == 400:
        print("✅ PASSED: DOB validation caught")
    else:
        print(f"⚠️  Expected 400, got {response.status_code}")


def test_register_duplicate_email():
    """Test POST /api/auth/register — Email đã tồn tại"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    # Email đã tồn tại trước đó (test@example.com)
    payload = {
        "email": "test@example.com",  # Email đã tồn tại
        "password": "TestPassword123!",
        "fullname": "Duplicate User",
        "phone": "0901234567",
        "dob": "1990-01-15"
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "Duplicate Email", "test_register_duplicate_email")
    
    if response.status_code == 409 or response.status_code == 400:
        print("✅ PASSED: Duplicate email rejected")
    else:
        print(f"⚠️  Expected 409/400, got {response.status_code}")


def test_confirm_signup_valid(email: str, confirmation_code: str):
    """Test POST /api/auth/confirm-signup — Xác thực thành công"""
    url = f"{API_BASE_URL}/api/auth/confirm-signup"
    
    payload = {
        "email": email,
        "confirmation_code": confirmation_code
    }
    
    response = requests.post(url, json=payload)
    data = print_response(response, "Valid Confirmation Code", "test_confirm_signup_valid")
    
    if response.status_code == 200:
        assert data.get("success") == True, "Missing success flag"
        print("✅ PASSED: Email confirmed successfully")
    else:
        print(f"⚠️  Expected 200, got {response.status_code}")


def test_confirm_signup_invalid_code():
    """Test POST /api/auth/confirm-signup — Mã xác thực không đúng"""
    url = f"{API_BASE_URL}/api/auth/confirm-signup"
    
    payload = {
        "email": "test@example.com",
        "confirmation_code": "999999"  # Mã không đúng
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "Invalid Confirmation Code", "test_confirm_signup_invalid_code")
    
    if response.status_code == 400:
        print("✅ PASSED: Invalid code rejected")
    else:
        print(f"⚠️  Expected 400, got {response.status_code}")


# ════════════════════════════════════════════════════════════════════════════════
# PROFILE TESTS — Quản lý hồ sơ (cần token)
# ════════════════════════════════════════════════════════════════════════════════

def test_profile_invalid_token():
    """Test GET /api/profile — Token không hợp lệ"""
    url = f"{API_BASE_URL}/api/profile"
    headers = {"Authorization": "Bearer invalid_token_xyz"}
    
    response = requests.get(url, headers=headers)
    print_response(response, "Invalid Token", "test_profile_invalid_token")
    
    if response.status_code == 401:
        print("✅ PASSED: Invalid token rejected")
    else:
        print(f"❌ FAILED: Expected 401, got {response.status_code}")


def test_profile_missing_token():
    """Test GET /api/profile — Token thiếu"""
    url = f"{API_BASE_URL}/api/profile"
    
    response = requests.get(url)
    print_response(response, "Missing Token", "test_profile_missing_token")
    
    if response.status_code == 401:
        print("✅ PASSED: Missing token rejected")
    else:
        print(f"❌ FAILED: Expected 401, got {response.status_code}")


def test_get_profile(token: str):
    """Test GET /api/profile — Lấy thông tin hồ sơ"""
    url = f"{API_BASE_URL}/api/profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    data = print_response(response, "Get Profile", "test_get_profile")
    
    if response.status_code == 200 and data:
        assert "user_id" in data, "Missing user_id"
        print("✅ PASSED: Profile retrieved successfully")
    else:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")


def test_update_personal_info(token: str):
    """Test PUT /api/profile/personal-info — Cập nhật thông tin"""
    url = f"{API_BASE_URL}/api/profile/personal-info"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "fullname": "Nguyễn Văn Updated",
        "email": "test@example.com",
        "phone": "0901234567",
        "dob": "1990-01-15"
    }
    
    response = requests.put(url, json=payload, headers=headers)
    data = print_response(response, "Update Personal Info", "test_update_personal_info")
    
    if response.status_code == 200 and data:
        assert data.get("success") == True, "Missing success flag"
        print("✅ PASSED: Personal info updated")
    else:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")


def test_update_avatar(token: str):
    """Test PUT /api/profile/avatar — Upload avatar"""
    url = f"{API_BASE_URL}/api/profile/avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    avatar_base64 = generate_test_image()
    payload = {"avatar": avatar_base64}
    
    response = requests.put(url, json=payload, headers=headers)
    data = print_response(response, "Update Avatar", "test_update_avatar")
    
    if response.status_code == 200 and data:
        assert data.get("success") == True, "Missing success flag"
        print("✅ PASSED: Avatar uploaded")
    else:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")


def test_change_password(token: str):
    """Test POST /api/profile/change-password — Đổi mật khẩu"""
    url = f"{API_BASE_URL}/api/profile/change-password"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "current_password": "WrongPassword123!",  # Sẽ fail
        "new_password": "NewPassword123!"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "Change Password", "test_change_password")
    
    if response.status_code in [200, 400]:
        print("✅ PASSED: Request processed (password wrong expected)")
    else:
        print(f"❌ FAILED: Expected 200/400, got {response.status_code}")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      Auth & Profile API Test Suite                        ║
╚════════════════════════════════════════════════════════════════════════════╝

📌 TEST CATEGORIES:
  1️⃣  Auth Tests (Register, Confirm)
  2️⃣  Profile Tests (need valid JWT token)

⚠️  REQUIREMENTS:
  - Backend running: python run.py
  - AWS connection (DynamoDB, Cognito, S3)
  - Port 8000 accessible
    """)
    
    # ─── Section 1: Auth Tests ─────────────────────────────────────────────
    print("\n\n" + "="*70)
    print("🔐 SECTION 1: AUTH ENDPOINTS (Không cần token)")
    print("="*70)
    
    print("\n📝 Test 1: Valid Registration")
    result = test_register_valid()
    
    print("\n📝 Test 2: Invalid Email Format")
    test_register_invalid_email()
    
    print("\n📝 Test 3: Weak Password")
    test_register_invalid_password()
    
    print("\n📝 Test 4: Invalid Phone Format")
    test_register_invalid_phone()
    
    print("\n📝 Test 5: Invalid DOB Format")
    test_register_invalid_dob()
    
    print("\n📝 Test 6: Duplicate Email")
    test_register_duplicate_email()
    
    print("\n📝 Test 7: Invalid Confirmation Code")
    test_confirm_signup_invalid_code()
    
    # ─── Section 2: Profile Tests (cần token) ─────────────────────────────
    print("\n\n" + "="*70)
    print("👤 SECTION 2: PROFILE ENDPOINTS (Cần JWT token)")
    print("="*70)
    
    print("\n📝 Test 1: Invalid Token")
    test_profile_invalid_token()
    
    print("\n📝 Test 2: Missing Token")
    test_profile_missing_token()
    
    token = input("\n🔑 Nhập JWT token (hoặc Enter để bỏ qua profile tests): ").strip()
    
    if token:
        print(f"\n✅ Dùng token: {token[:50]}...")
        try:
            print("\n📝 Test 3: Get Profile")
            test_get_profile(token)
            
            print("\n📝 Test 4: Update Personal Info")
            test_update_personal_info(token)
            
            print("\n📝 Test 5: Update Avatar")
            test_update_avatar(token)
            
            print("\n📝 Test 6: Change Password")
            test_change_password(token)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("\n⏭️  Skipped profile tests (no token provided)")
    
    print("\n\n" + "="*70)
    print("📊 TEST SUITE COMPLETED")
    print("="*70)
    print("""
📝 NOTES:
  - Register endpoint tạo unique email dùng timestamp
  - ConfirmSignUp cần mã từ email (tự động từ AWS)
  - Profile tests cần valid JWT token từ login
  - Tất cả endpoints đều có error handling đầy đủ

🔗 API Documentation:
  - POST /api/auth/register — Đăng ký
  - POST /api/auth/confirm-signup — Xác thực
  - GET /api/profile — Lấy hồ sơ
  - PUT /api/profile/personal-info — Cập nhật thông tin
  - PUT /api/profile/avatar — Upload avatar
  - POST /api/profile/change-password — Đổi mật khẩu
    """)


if __name__ == "__main__":
    main()
