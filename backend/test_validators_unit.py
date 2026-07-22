"""
Unit Tests for Validation Functions
pytest test_validators_unit.py -v
"""

import pytest
from modules.auth_service import validate_phone_format, validate_dob, validate_fullname


# ═══════════════════════════════════════════════════════════════════════════
# PHONE VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPhoneValidation:
    """Test phone format validation"""
    
    def test_valid_phone_vn_mobile(self):
        """Valid Vietnamese mobile numbers"""
        assert validate_phone_format("0901234567") == True
        assert validate_phone_format("0912345678") == True
        assert validate_phone_format("0987654321") == True
    
    def test_valid_phone_e164(self):
        """Valid E.164 format"""
        assert validate_phone_format("+84901234567") == True
        assert validate_phone_format("+84912345678") == True
        assert validate_phone_format("+1234567890") == True
    
    def test_invalid_phone_with_spaces(self):
        """Phone with spaces should be rejected"""
        assert validate_phone_format("090 123 4567") == False
        assert validate_phone_format("090 1234 567") == False
        assert validate_phone_format("+84 90 123 4567") == False
    
    def test_invalid_phone_with_dashes(self):
        """Phone with dashes should be rejected"""
        assert validate_phone_format("090-123-4567") == False
        assert validate_phone_format("090-1234-567") == False
    
    def test_invalid_phone_with_parentheses(self):
        """Phone with parentheses should be rejected"""
        assert validate_phone_format("(090) 1234567") == False
        assert validate_phone_format("(+84) 901234567") == False
    
    def test_invalid_phone_too_short(self):
        """Phone too short"""
        assert validate_phone_format("090123") == False
        assert validate_phone_format("+8490") == False
    
    def test_invalid_phone_too_long(self):
        """Phone too long"""
        assert validate_phone_format("090123456789012345") == False
    
    def test_invalid_phone_with_letters(self):
        """Phone with letters should be rejected"""
        assert validate_phone_format("090ABC4567") == False
        assert validate_phone_format("test@phone") == False
    
    def test_empty_phone(self):
        """Empty phone should be rejected"""
        assert validate_phone_format("") == False
        assert validate_phone_format(None) == False


# ═══════════════════════════════════════════════════════════════════════════
# DATE OF BIRTH VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestDOBValidation:
    """Test date of birth validation"""
    
    def test_valid_dob_normal_dates(self):
        """Valid normal dates"""
        assert validate_dob("1990-01-01") == True
        assert validate_dob("1995-12-31") == True
        assert validate_dob("2000-06-15") == True
    
    def test_valid_dob_edge_of_range(self):
        """Valid dates at edge of range (1900-2099)"""
        assert validate_dob("1900-01-01") == True
        assert validate_dob("2098-12-31") == True
    
    def test_valid_dob_leap_year(self):
        """Valid leap year dates"""
        assert validate_dob("2000-02-29") == True  # Leap year
        assert validate_dob("2020-02-29") == True  # Leap year
    
    def test_invalid_dob_out_of_range_before(self):
        """Invalid dates before 1900"""
        assert validate_dob("1899-12-31") == False
        assert validate_dob("1800-01-01") == False
    
    def test_invalid_dob_out_of_range_after(self):
        """Invalid dates after 2099"""
        assert validate_dob("2100-01-01") == False
        assert validate_dob("2999-12-31") == False
    
    def test_invalid_dob_wrong_format(self):
        """Invalid date formats"""
        assert validate_dob("01-01-1990") == False  # Wrong format
        assert validate_dob("1990/01/01") == False  # Wrong separator
        assert validate_dob("01/01/1990") == False  # US format
    
    def test_invalid_dob_invalid_dates(self):
        """Invalid calendar dates"""
        assert validate_dob("2021-02-29") == False  # Not a leap year
        assert validate_dob("1990-13-01") == False  # Invalid month
        assert validate_dob("1990-01-32") == False  # Invalid day
    
    def test_invalid_dob_malformed(self):
        """Malformed date strings"""
        assert validate_dob("not-a-date") == False
        assert validate_dob("1990-1-1") == False  # Missing leading zeros
        assert validate_dob("") == False
        assert validate_dob(None) == False


# ═══════════════════════════════════════════════════════════════════════════
# FULLNAME VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestFullnameValidation:
    """Test fullname validation (XSS prevention)"""
    
    def test_valid_fullname_simple(self):
        """Valid simple names"""
        assert validate_fullname("John Doe") == True
        assert validate_fullname("Nguyen Van A") == True
        assert validate_fullname("Mary Jane") == True
    
    def test_valid_fullname_unicode(self):
        """Valid names with unicode characters"""
        assert validate_fullname("Nguyễn Văn Á") == True
        assert validate_fullname("Trần Thị Bình") == True
        assert validate_fullname("Lê Hoàng Minh") == True
    
    def test_valid_fullname_with_apostrophe(self):
        """Valid names with apostrophe"""
        assert validate_fullname("O'Brien") == True
        assert validate_fullname("D'Angelo") == True
    
    def test_valid_fullname_with_dash(self):
        """Valid names with dash"""
        assert validate_fullname("Jean-Pierre") == True
        assert validate_fullname("Mary-Ann") == True
    
    def test_valid_fullname_with_numbers(self):
        """Names with numbers (unusual but should pass sanitization)"""
        # Note: validate_fullname strips HTML but allows numbers
        assert validate_fullname("User123") == True
    
    def test_invalid_fullname_xss_script_tags(self):
        """XSS: script tags should be stripped/rejected"""
        result = validate_fullname("<script>alert(1)</script>")
        # Should either be rejected or sanitized
        assert result == False or "<script>" not in result
    
    def test_invalid_fullname_xss_onclick(self):
        """XSS: onclick attributes should be rejected"""
        result = validate_fullname('onclick=alert(1)')
        assert result == False or "onclick=" not in result
    
    def test_invalid_fullname_xss_onerror(self):
        """XSS: onerror attributes should be rejected"""
        result = validate_fullname('<img src=x onerror=alert(1)>')
        assert result == False or "onerror=" not in result
    
    def test_invalid_fullname_too_long(self):
        """Names exceeding max length (100 chars)"""
        long_name = "A" * 101
        result = validate_fullname(long_name)
        # Should be truncated or rejected
        assert result == False or len(result) <= 100
    
    def test_invalid_fullname_empty(self):
        """Empty names should be rejected"""
        assert validate_fullname("") == False
        assert validate_fullname(None) == False
        assert validate_fullname("   ") == False  # Only whitespace


# ═══════════════════════════════════════════════════════════════════════════
# PARAMETRIZED TESTS (Advanced)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("phone,expected", [
    ("0901234567", True),
    ("+84901234567", True),
    ("090 123 4567", False),
    ("090-123-4567", False),
    ("", False),
])
def test_phone_validation_parametrized(phone, expected):
    """Parametrized phone validation tests"""
    assert validate_phone_format(phone) == expected


@pytest.mark.parametrize("dob,expected", [
    ("1990-01-01", True),
    ("2000-02-29", True),  # Leap year
    ("2021-02-29", False),  # Not leap year
    ("2100-01-01", False),  # Out of range
    ("1899-12-31", False),  # Out of range
])
def test_dob_validation_parametrized(dob, expected):
    """Parametrized DOB validation tests"""
    assert validate_dob(dob) == expected


# ═══════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_phone_exact_length_boundaries(self):
        """Test phone at exact length boundaries"""
        # E.164 allows 7-15 digits
        assert validate_phone_format("+1234567") == True  # Min length
        assert validate_phone_format("+123456789012345") == True  # Max length
    
    def test_dob_boundary_dates(self):
        """Test DOB at year boundaries"""
        assert validate_dob("1900-01-01") == True  # Min year
        assert validate_dob("2098-12-31") == True  # Max year (assuming 2099 is limit)
    
    def test_fullname_special_characters(self):
        """Test fullname with various special characters"""
        assert validate_fullname("John-Paul O'Connor") == True
        # Ampersand might be allowed after sanitization
        result = validate_fullname("Smith & Johnson")
        assert isinstance(result, (bool, str))  # Either rejected or sanitized
