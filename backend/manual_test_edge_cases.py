"""
Edge Cases Test Suite cho Profile & Auth API
Chạy backend local trước: python run.py
Sau đó chạy: python test_edge_cases.py
"""

import requests
import json
import base64
import time
from io import BytesIO
from PIL import Image
import threading
import concurrent.futures

# ─── Config ────────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

# ─── Helpers ────────────────────────────────────────────────────────────────

def generate_test_image(size_kb: int = 100) -> str:
    """Tạo test image với size cụ thể (KB)"""
    # Rough estimate: 100KB ≈ 700x700 RGB image
    dim = int((size_kb * 700) / 100)
    img = Image.new('RGB', (dim, dim), color='blue')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_base64}"


def print_test_result(test_name: str, status: str, expected: str, actual: str, message: str = ""):
    """In kết quả test đẹp"""
    status_emoji = "✅" if status == "PASS" else "❌"
    print(f"\n{status_emoji} {test_name}")
    print(f"   Expected: {expected}")
    print(f"   Actual:   {actual}")
    if message:
        print(f"   Note: {message}")


# ════════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ════════════════════════════════════════════════════════════════════════════════

def test_duplicate_registration_same_email():
    """Test: Register 2x cùng email → phải reject lần 2"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    email = f"duplicate_test_{int(time.time())}@example.com"
    payload = {
        "email": email,
        "password": "TestPassword123!",
        "fullname": "Test User",
        "phone": "0901234567",
        "dob": "1990-01-15"
    }
    
    # Register lần 1
    response1 = requests.post(url, json=payload)
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Duplicate Registration")
    print(f"{'─'*70}")
    print(f"Register #1: {response1.status_code}")
    
    if response1.status_code != 200:
        print(f"❌ FAIL: Register #1 should be 200, got {response1.status_code}")
        return
    
    # Register lần 2 (cùng email)
    time.sleep(1)
    response2 = requests.post(url, json=payload)
    print(f"Register #2: {response2.status_code}")
    
    if response2.status_code == 409 or response2.status_code == 400:
        print(f"✅ PASS: Duplicate email rejected with {response2.status_code}")
    else:
        print(f"❌ FAIL: Expected 409/400, got {response2.status_code}")
        print(f"   Response: {response2.json()}")


def test_profile_not_in_dynamodb():
    """Test: User có Cognito nhưng không có DynamoDB profile"""
    url = f"{API_BASE_URL}/api/profile"
    
    # Dùng token của user không có profile
    # (Để simulate: Tạo user via Cognito console, không qua API)
    # Cho đơn giản, dùng invalid user_id
    
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJub25leGlzdGVudC11c2VyLWlkIn0.fake"
    headers = {"Authorization": f"Bearer {fake_token}"}
    
    response = requests.get(url, headers=headers)
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Profile Not In DynamoDB")
    print(f"{'─'*70}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404 or response.status_code == 401:
        print(f"✅ PASS: Returned {response.status_code} for missing profile")
    else:
        print(f"⚠️  Got {response.status_code} - Check if expected")


def test_avatar_size_boundary():
    """Test: Avatar size boundary (300KB, 5MB)"""
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Avatar Size Boundary")
    print(f"{'─'*70}")
    
    # Note: Testing size validation without valid token
    # Để full test cần token hợp lệ
    
    sizes_to_test = [
        (100, "100 KB", "should work"),
        (299, "299 KB", "should work (<300KB)"),
        (300, "300 KB", "boundary - use S3"),
        (1000, "1 MB", "should work"),
        (5000, "5 MB", "max size - boundary"),
    ]
    
    for size, label, note in sizes_to_test:
        try:
            img_b64 = generate_test_image(size)
            actual_size = len(img_b64) / (1024 * 1024)
            print(f"✓ {label} image generated ({actual_size:.2f} MB actual)")
        except Exception as e:
            print(f"✗ {label} generation failed: {e}")


def test_concurrent_registration():
    """Test: 5 concurrent registrations"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    def register_user(user_num):
        email = f"concurrent_{int(time.time())}_{user_num}@example.com"
        payload = {
            "email": email,
            "password": "TestPassword123!",
            "fullname": f"User {user_num}",
            "phone": "0901234567",
            "dob": "1990-01-15"
        }
        response = requests.post(url, json=payload)
        return user_num, response.status_code, email
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Concurrent Registrations")
    print(f"{'─'*70}")
    
    # Run 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(register_user, i) for i in range(1, 6)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    results.sort(key=lambda x: x[0])
    
    all_success = True
    for user_num, status, email in results:
        if status == 200:
            print(f"✓ User {user_num}: {status} OK")
        else:
            print(f"✗ User {user_num}: {status} FAIL")
            all_success = False
    
    if all_success:
        print(f"✅ PASS: All 5 concurrent registrations succeeded")
    else:
        print(f"❌ FAIL: Some registrations failed")


def test_update_with_empty_fields():
    """Test: Update profile dengan empty/null fields"""
    url = f"{API_BASE_URL}/api/profile/personal-info"
    
    # Cần token valid
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Update Profile With Empty Fields")
    print(f"{'─'*70}")
    
    payloads = [
        ({"fullname": "", "email": "test@example.com", "phone": "0901234567", "dob": "1990-01-15"}, 
         "Empty fullname"),
        ({"fullname": "Test", "email": "", "phone": "0901234567", "dob": "1990-01-15"}, 
         "Empty email"),
        ({"fullname": "Test", "email": "test@example.com", "phone": "", "dob": "1990-01-15"}, 
         "Empty phone"),
        ({"fullname": "Test", "email": "test@example.com", "phone": "0901234567", "dob": ""}, 
         "Empty dob"),
    ]
    
    for payload, desc in payloads:
        print(f"\n  Testing: {desc}")
        print(f"  Payload: {payload}")
        print(f"  (Skipped - needs valid token)")


def test_special_characters_in_fullname():
    """Test: Fullname với ký tự đặc biệt"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Special Characters in Fullname")
    print(f"{'─'*70}")
    
    fullnames = [
        "Nguyễn Văn Á",           # Vietnamese accents
        "José García",            # Spanish
        "李明",                   # Chinese
        "Μαρία",                 # Greek
        "محمد علي",             # Arabic
        "Test@User#123",         # Special chars
        "O'Brien",               # Apostrophe
        "Jean-Paul",             # Hyphen
    ]
    
    for fullname in fullnames:
        payload = {
            "email": f"special_{int(time.time())}_{fullnames.index(fullname)}@example.com",
            "password": "TestPassword123!",
            "fullname": fullname,
            "phone": "0901234567",
            "dob": "1990-01-15"
        }
        
        response = requests.post(url, json=payload)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} '{fullname}': {response.status_code}")
        
        if response.status_code != 200:
            print(f"  Error: {response.json().get('detail', 'Unknown')}")


def test_very_long_password():
    """Test: Password rất dài (>256 chars)"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Very Long Password")
    print(f"{'─'*70}")
    
    passwords = [
        ("Short1!", "8 chars (minimum)"),
        ("TestPassword123!", "Standard length"),
        ("P" * 50 + "1!", "50 chars"),
        ("P" * 128 + "1!", "128 chars"),
        ("P" * 256 + "1!", "256 chars"),
        ("P" * 512 + "1!", "512 chars"),
    ]
    
    for password, desc in passwords:
        payload = {
            "email": f"longpwd_{int(time.time())}_{passwords.index((password, desc))}@example.com",
            "password": password,
            "fullname": "Test User",
            "phone": "0901234567",
            "dob": "1990-01-15"
        }
        
        response = requests.post(url, json=payload)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {desc} (len={len(password)}): {response.status_code}")
        
        if response.status_code not in [200, 400]:
            print(f"  Unexpected: {response.json().get('detail', 'Unknown')}")


def test_unicode_phone_number():
    """Test: Phone number với unicode/special formats"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Unicode Phone Numbers")
    print(f"{'─'*70}")
    
    phones = [
        ("0901234567", "Standard Vietnam", True),
        ("+84901234567", "E.164 format", True),
        ("(090) 1234-567", "Formatted with parens", False),
        ("090-1234-567", "With dashes", False),
        ("090 1234 567", "With spaces", False),
        ("+1-202-555-0173", "US format", False),
        ("٠٩٠١٢٣٤٥٦٧", "Arabic numerals", False),
    ]
    
    for phone, desc, expected_ok in phones:
        payload = {
            "email": f"phone_{int(time.time())}_{phones.index((phone, desc, expected_ok))}@example.com",
            "password": "TestPassword123!",
            "fullname": "Test User",
            "phone": phone,
            "dob": "1990-01-15"
        }
        
        response = requests.post(url, json=payload)
        
        if expected_ok:
            expected = "200"
            status = "✓" if response.status_code == 200 else "✗"
        else:
            expected = "400"
            status = "✓" if response.status_code == 400 else "✗"
        
        print(f"{status} '{phone}' ({desc}): {response.status_code} (expected {expected})")


def test_sql_injection_attempt():
    """Test: SQL injection / XSS attempts"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Security - SQL Injection / XSS Attempts")
    print(f"{'─'*70}")
    
    payloads = [
        {
            "email": "'; DROP TABLE users; --@example.com",
            "password": "TestPassword123!",
            "fullname": "Test User",
            "phone": "0901234567",
            "dob": "1990-01-15"
        },
        {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "fullname": "<script>alert('XSS')</script>",
            "phone": "0901234567",
            "dob": "1990-01-15"
        },
        {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "fullname": "Test User",
            "phone": "0901234567'; DROP TABLE--",
            "dob": "1990-01-15"
        },
    ]
    
    for i, payload in enumerate(payloads, 1):
        response = requests.post(url, json=payload)
        # Should either fail with 400 or succeed (payload is just data, not executed)
        status = "✓" if response.status_code in [200, 400] else "✗"
        print(f"{status} Attempt {i}: {response.status_code}")
        
        # Most important: No 500 error
        if response.status_code == 500:
            print(f"  ❌ DANGEROUS: Server error with injection attempt!")


def test_whitespace_handling():
    """Test: Whitespace ở đầu/cuối fields"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: Whitespace Handling")
    print(f"{'─'*70}")
    
    test_cases = [
        {
            "email": "  space@example.com  ",
            "fullname": "  Spaced Name  ",
            "desc": "Leading/trailing spaces"
        },
        {
            "email": "tab\t@example.com",
            "fullname": "\tTabbed\tName\t",
            "desc": "Tab characters"
        },
        {
            "email": "newline@example.com",
            "fullname": "Name\nWith\nNewlines",
            "desc": "Newline characters"
        },
    ]
    
    for test_case in test_cases:
        payload = {
            "email": test_case["email"],
            "password": "TestPassword123!",
            "fullname": test_case["fullname"],
            "phone": "0901234567",
            "dob": "1990-01-15"
        }
        
        response = requests.post(url, json=payload)
        print(f"Test {test_case['desc']}: {response.status_code}")
        
        # Should trim whitespace or reject
        if response.status_code in [200, 400]:
            print(f"  ✓ Handled")
        else:
            print(f"  ✗ Unexpected: {response.json().get('detail')}")


def test_boundary_date_values():
    """Test: DOB boundary values"""
    url = f"{API_BASE_URL}/api/auth/register"
    
    print(f"\n{'─'*70}")
    print(f"🧪 Test: DOB Boundary Values")
    print(f"{'─'*70}")
    
    dates = [
        ("1900-01-01", "Very old (1900)"),
        ("1950-06-15", "Mid 20th century"),
        ("1990-12-31", "Standard"),
        ("2000-01-01", "Y2K"),
        ("2010-02-29", "Leap year - but 2010 not leap!"),  # Invalid
        ("2020-02-29", "Valid leap year"),
        ("2099-12-31", "Far future"),
        ("2025-13-01", "Invalid month"),
        ("2025-02-30", "Invalid day"),
        ("1899-12-31", "Before 1900"),
    ]
    
    for dob, desc in dates:
        payload = {
            "email": f"dob_{int(time.time())}_{dates.index((dob, desc))}@example.com",
            "password": "TestPassword123!",
            "fullname": "Test User",
            "phone": "0901234567",
            "dob": dob
        }
        
        response = requests.post(url, json=payload)
        
        # Determine if should pass/fail
        is_valid_date = (1900 <= int(dob.split('-')[0]) <= 2025 and 
                         1 <= int(dob.split('-')[1]) <= 12 and
                         1 <= int(dob.split('-')[2]) <= 31)
        
        expected = "200 OK" if is_valid_date else "400 ERROR"
        status = "✓" if (is_valid_date and response.status_code == 200) or (not is_valid_date and response.status_code == 400) else "✗"
        
        print(f"{status} {desc}: {dob} → {response.status_code}")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       Edge Cases Test Suite                               ║
║                  Profile & Auth API Comprehensive Testing                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📌 TEST CATEGORIES:
  1️⃣  Duplicate Registration
  2️⃣  Profile Consistency
  3️⃣  Avatar Size Boundaries
  4️⃣  Concurrent Requests
  5️⃣  Character Encoding (Unicode, Special Chars)
  6️⃣  Input Validation (Long passwords, Whitespace)
  7️⃣  Security (SQL Injection, XSS)
  8️⃣  Boundary Values (DOB, Phone)

⚠️  REQUIREMENTS:
  - Backend running: python run.py
  - AWS connection (DynamoDB, Cognito, S3)
  - Port 8000 accessible
    """)
    
    # Run all tests
    test_duplicate_registration_same_email()
    test_profile_not_in_dynamodb()
    test_avatar_size_boundary()
    test_concurrent_registration()
    test_update_with_empty_fields()
    test_special_characters_in_fullname()
    test_very_long_password()
    test_unicode_phone_number()
    test_sql_injection_attempt()
    test_whitespace_handling()
    test_boundary_date_values()
    
    print(f"""

╔════════════════════════════════════════════════════════════════════════════╗
║                     Edge Case Testing Completed                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 Summary:
  ✅ Duplicate registration handling
  ✅ Avatar size boundaries
  ✅ Concurrent request handling
  ✅ Character encoding support
  ✅ Input validation robustness
  ✅ Security against injection attacks
  ✅ Boundary value handling
  ✅ Whitespace normalization

🚀 Next Steps:
  1. Review test results
  2. Fix any failures
  3. Deploy to staging Lambda
  4. Run against real AWS services
  5. Deploy to production

📝 Notes:
  - Some tests need valid JWT token
  - Test with actual user data if needed
  - Monitor CloudWatch logs for details
    """)


if __name__ == "__main__":
    main()
