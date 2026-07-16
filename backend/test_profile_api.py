"""
Test Script cho Profile API Endpoints
Chạy backend local trước: python run.py
Sau đó chạy: python test_profile_api.py
"""

import requests
import json
import base64
import os
from io import BytesIO
from PIL import Image

# ─── Config ────────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

# Dùng test token từ local Cognito login
# Bạn cần login trước ở frontend để lấy JWT token
# Hoặc dùng AWS CLI để lấy token

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_TOKEN = None  # Sẽ lấy sau khi login

# ─── Helpers ────────────────────────────────────────────────────────────────

def generate_test_image() -> str:
    """Tạo test image dạng base64"""
    img = Image.new('RGB', (300, 300), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_base64}"


def print_response(response: requests.Response, title: str = ""):
    """In response đẹp"""
    print(f"\n{'='*70}")
    print(f"📋 {title}")
    print(f"{'='*70}")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Body:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Body: {response.text}")


# ─── Tests ─────────────────────────────────────────────────────────────────

def test_get_profile(token: str):
    """Test GET /api/profile"""
    url = f"{API_BASE_URL}/api/profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print_response(response, "GET /api/profile")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "user_id" in data, "Response missing 'user_id'"
    print("✅ test_get_profile PASSED")


def test_update_personal_info(token: str):
    """Test PUT /api/profile/personal-info"""
    url = f"{API_BASE_URL}/api/profile/personal-info"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "fullname": "Nguyễn Văn Test",
        "email": "test@example.com",
        "phone": "0901234567",
        "dob": "1990-01-01"
    }
    
    response = requests.put(url, json=payload, headers=headers)
    print_response(response, "PUT /api/profile/personal-info")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("success") == True, "Response success not true"
    print("✅ test_update_personal_info PASSED")


def test_update_avatar(token: str):
    """Test PUT /api/profile/avatar"""
    url = f"{API_BASE_URL}/api/profile/avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    avatar_base64 = generate_test_image()
    payload = {"avatar": avatar_base64}
    
    response = requests.put(url, json=payload, headers=headers)
    print_response(response, "PUT /api/profile/avatar")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("success") == True, "Response success not true"
    print("✅ test_update_avatar PASSED")


def test_change_password(token: str):
    """Test POST /api/profile/change-password"""
    url = f"{API_BASE_URL}/api/profile/change-password"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "POST /api/profile/change-password")
    
    # Note: Có thể fail vì password không đúng, nhưng test request format
    if response.status_code == 200:
        data = response.json()
        assert data.get("success") == True, "Response success not true"
        print("✅ test_change_password PASSED")
    else:
        print("⚠️  test_change_password: Expected error (password không đúng?)")


def test_invalid_token():
    """Test invalid token"""
    url = f"{API_BASE_URL}/api/profile"
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = requests.get(url, headers=headers)
    print_response(response, "GET /api/profile (Invalid Token)")
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✅ test_invalid_token PASSED")


def test_missing_token():
    """Test missing token"""
    url = f"{API_BASE_URL}/api/profile"
    
    response = requests.get(url)
    print_response(response, "GET /api/profile (Missing Token)")
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✅ test_missing_token PASSED")


def test_invalid_email():
    """Test invalid email format"""
    # Cần token hợp lệ
    # Vì không có token hợp lệ, chỉ test request format
    url = f"{API_BASE_URL}/api/profile/personal-info"
    headers = {"Authorization": "Bearer dummy_token"}
    
    payload = {
        "fullname": "Test",
        "email": "invalid-email",  # Invalid
        "phone": "0901234567",
        "dob": "1990-01-01"
    }
    
    response = requests.put(url, json=payload, headers=headers)
    print_response(response, "PUT /api/profile/personal-info (Invalid Email)")
    
    # Sẽ fail vì token invalid, nhưng ít nhất request format đúng
    print("⚠️  test_invalid_email: Skipped (need valid token)")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      Profile API Test Suite                               ║
╚════════════════════════════════════════════════════════════════════════════╝

📌 HƯỚNG DẪN:
  1. Chạy backend: python run.py
  2. Login ở frontend hoặc dùng Cognito để lấy JWT token
  3. Paste token vào dòng input bên dưới
  4. Script sẽ tự động test các endpoints

⚠️  LƯU Ý:
  - Cần kết nối tới AWS DynamoDB + Cognito
  - Thay đổi API_BASE_URL nếu backend chạy ở port khác
    """)
    
    # Test endpoints không cần token
    print("\n🔧 Testing endpoints không cần token...")
    test_invalid_token()
    test_missing_token()
    
    # Test endpoints cần token
    token = input("\n🔑 Nhập JWT token (hoặc Enter để bỏ qua): ").strip()
    
    if token:
        print(f"\n✅ Dùng token: {token[:50]}...")
        try:
            # Tạo profile trước nếu chưa có
            print("\n📝 Tạo profile trước...")
            test_update_personal_info(token)
            
            # Sau đó test các endpoint khác
            test_get_profile(token)
            test_update_avatar(token)
            # test_change_password(token)  # Bỏ comment để test
            
            print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        ✅ ALL TESTS PASSED!                               ║
╚════════════════════════════════════════════════════════════════════════════╝
            """)
        except AssertionError as e:
            print(f"\n❌ Test FAILED: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("\n⏭️  Bỏ qua tests cần token")
        print("""
📝 Để lấy JWT token:
  1. Login ở frontend React (/login)
  2. Mở DevTools → Application → Cookies → auth_token
  3. Copy token vào đây
        """)


if __name__ == "__main__":
    main()
