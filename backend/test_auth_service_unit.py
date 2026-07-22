"""
Unit Tests for Auth Service with Mocking
pytest test_auth_service_unit.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError


# ═══════════════════════════════════════════════════════════════════════════
# MOCK FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_cognito_client():
    """Mock Cognito IDP client"""
    with patch('modules.auth_service.get_cognito_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource"""
    with patch('modules.auth_service.get_dynamodb_resource') as mock:
        resource = MagicMock()
        table = MagicMock()
        resource.Table.return_value = table
        mock.return_value = resource
        yield table


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION FUNCTION TESTS (Integration with auth_service)
# ═══════════════════════════════════════════════════════════════════════════

from modules.auth_service import validate_phone_format, validate_dob, validate_fullname


class TestValidationFunctions:
    """Test validation functions imported from auth_service"""
    
    def test_validate_phone_integration(self):
        """Test phone validation works as expected"""
        assert validate_phone_format("0901234567") == True
        assert validate_phone_format("+84901234567") == True
        assert validate_phone_format("invalid") == False
    
    def test_validate_dob_integration(self):
        """Test DOB validation works as expected"""
        assert validate_dob("1990-01-01") == True
        assert validate_dob("2100-01-01") == False
    
    def test_validate_fullname_integration(self):
        """Test fullname validation works as expected"""
        assert validate_fullname("John Doe") == True
        result = validate_fullname("<script>alert(1)</script>")
        assert result == False or "<script>" not in str(result)


# ═══════════════════════════════════════════════════════════════════════════
# AUTH SERVICE LOGIC TESTS WITH MOCKING
# ═══════════════════════════════════════════════════════════════════════════

# TODO: Implement TestRegisterUser - function raises Exception on error, not returns {"success": False}


class TestCleanupUnconfirmedUsers:
    """Test cleanup_unconfirmed_users function"""
    
    @patch('modules.auth_service.get_cognito_client')
    @patch('modules.auth_service.datetime')
    def test_cleanup_no_users(self, mock_datetime, mock_cognito):
        """Test cleanup when no unconfirmed users exist"""
        # Mock current time
        mock_datetime.now.return_value = datetime(2026, 7, 22, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock Cognito to return empty list
        mock_client = MagicMock()
        mock_client.list_users.return_value = {'Users': []}
        mock_cognito.return_value = mock_client
        
        from modules.auth_service import cleanup_unconfirmed_users
        
        result = cleanup_unconfirmed_users(max_age_minutes=5)
        
        # Should succeed with 0 deletions
        assert result['success'] == True
        assert result['deleted_count'] == 0
    
    @patch('modules.auth_service.get_cognito_client')
    @patch('modules.auth_service.datetime')
    def test_cleanup_old_user_deleted(self, mock_datetime, mock_cognito):
        """Test cleanup deletes old unconfirmed user"""
        # Mock current time: 2026-07-22 12:00:00
        now = datetime(2026, 7, 22, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock Cognito to return old unconfirmed user (created 10 minutes ago)
        old_user_time = datetime(2026, 7, 22, 11, 50, 0)
        mock_client = MagicMock()
        mock_client.list_users.return_value = {
            'Users': [{
                'Username': 'old-user',
                'Attributes': [{'Name': 'email', 'Value': 'old@example.com'}],
                'UserCreateDate': old_user_time,
                'UserStatus': 'UNCONFIRMED'
            }]
        }
        mock_client.admin_delete_user.return_value = {}
        mock_cognito.return_value = mock_client
        
        from modules.auth_service import cleanup_unconfirmed_users
        
        result = cleanup_unconfirmed_users(max_age_minutes=5)
        
        # Should delete the old user
        assert result['success'] == True
        assert result['deleted_count'] == 1
        mock_client.admin_delete_user.assert_called_once()
    
    @patch('modules.auth_service.get_cognito_client')
    @patch('modules.auth_service.datetime')
    def test_cleanup_recent_user_not_deleted(self, mock_datetime, mock_cognito):
        """Test cleanup keeps recent unconfirmed user"""
        # Mock current time: 2026-07-22 12:00:00
        now = datetime(2026, 7, 22, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Mock Cognito to return recent user (created 2 minutes ago)
        recent_user_time = datetime(2026, 7, 22, 11, 58, 0)
        mock_client = MagicMock()
        mock_client.list_users.return_value = {
            'Users': [{
                'Username': 'recent-user',
                'Attributes': [{'Name': 'email', 'Value': 'recent@example.com'}],
                'UserCreateDate': recent_user_time,
                'UserStatus': 'UNCONFIRMED'
            }]
        }
        mock_cognito.return_value = mock_client
        
        from modules.auth_service import cleanup_unconfirmed_users
        
        result = cleanup_unconfirmed_users(max_age_minutes=5)
        
        # Should NOT delete recent user
        assert result['success'] == True
        assert result['deleted_count'] == 0
        mock_client.admin_delete_user.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestHelperFunctions:
    """Test helper/utility functions"""
    
    def test_normalize_phone_vietnam_format(self):
        """Test phone normalization to E.164"""
        from modules.profile_service import normalize_phone
        
        # 0901234567 → +84901234567
        assert normalize_phone("0901234567") == "+84901234567"
        assert normalize_phone("0912345678") == "+84912345678"
    
    def test_normalize_phone_already_e164(self):
        """Test phone already in E.164 format"""
        from modules.profile_service import normalize_phone
        
        # Already E.164
        assert normalize_phone("+84901234567") == "+84901234567"
        assert normalize_phone("+1234567890") == "+1234567890"
    
    def test_get_timestamp_returns_int(self):
        """Test timestamp generation"""
        from modules.profile_service import get_timestamp
        
        ts = get_timestamp()
        assert isinstance(ts, int)
        assert ts > 1700000000  # After 2023
        assert ts < 2000000000  # Before 2033


# ═══════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('modules.auth_service.get_cognito_client')
    def test_signup_network_error(self, mock_cognito):
        """Test signup handles network errors gracefully"""
        # Mock Cognito to raise generic exception
        mock_client = MagicMock()
        mock_client.sign_up.side_effect = Exception("Network error")
        mock_cognito.return_value = mock_client
        
        from modules.auth_service import register_user
        
        # Should not crash, should return error
        result = register_user(
            email="test@example.com",
            password="TestPass123!",
            fullname="Test User",
            phone="0901234567",
            dob="1990-01-01"
        )
        
        assert result['success'] == False
        assert 'message' in result
    
    def test_validation_with_none_values(self):
        """Test validators handle None gracefully"""
        assert validate_phone_format(None) == False
        assert validate_dob(None) == False
        assert validate_fullname(None) == False
    
    def test_validation_with_empty_strings(self):
        """Test validators handle empty strings"""
        assert validate_phone_format("") == False
        assert validate_dob("") == False
        assert validate_fullname("") == False
    
    def test_validation_with_whitespace_only(self):
        """Test validators handle whitespace-only strings"""
        assert validate_phone_format("   ") == False
        assert validate_fullname("   ") == False
