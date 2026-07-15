"""
[SmartDocAI-Auth] auth_service.py
Dịch vụ xác thực: Register, Login, Confirm Code, etc.
Tích hợp Cognito + DynamoDB
"""

import boto3
import logging
import re
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from config import AWS_DEFAULT_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, DYNAMODB_USERS_TABLE
from .profile_service import (
    get_dynamodb_resource,
    normalize_phone,
    get_timestamp
)

logger = logging.getLogger("SmartDocAI_Auth")

# ─── Singleton Cognito Client ────────────────────────────────────────────────
_cognito_client = None

def get_cognito_client():
    """[Helper] Lấy Cognito IDP client (singleton)"""
    global _cognito_client
    if not _cognito_client:
        _cognito_client = boto3.client('cognito-idp', region_name=AWS_DEFAULT_REGION)
    return _cognito_client


# ─── Validation Functions ────────────────────────────────────────────────────

def validate_phone_format(phone: str) -> bool:
    """
    [Validator] Kiểm tra format số điện thoại
    Chỉ accept:
    - 0901234567 (10 digits, bắt đầu bằng 0)
    - +84901234567 (E.164 format, 12 digits)
    
    Returns: True nếu valid, False nếu invalid
    """
    if not phone:
        return False
    
    phone = phone.strip()
    
    # Vietnam format: 0 + 9 digits (0901234567)
    if re.match(r'^0\d{9}$', phone):
        return True
    
    # E.164 format: +84 + 9 digits (+84901234567)
    if re.match(r'^\+84\d{9}$', phone):
        return True
    
    return False


def validate_fullname(fullname: str) -> bool:
    """
    [Validator] Kiểm tra tên người dùng
    - Từ 2-100 ký tự
    - Không chứa HTML tags hoặc special characters nguy hiểm
    
    Returns: True nếu valid, False nếu invalid
    """
    if not fullname:
        return False
    
    fullname = fullname.strip()
    
    # Length check
    if len(fullname) < 2 or len(fullname) > 100:
        return False
    
    # Block HTML/script tags
    dangerous_patterns = [r'<', r'>', r'script', r'onclick', r'javascript:', r'on\w+\s*=']
    for pattern in dangerous_patterns:
        if re.search(pattern, fullname, re.IGNORECASE):
            return False
    
    return True


def validate_dob(dob: str) -> bool:
    """
    [Validator] Kiểm tra ngày sinh
    - Format: YYYY-MM-DD
    - Năm: 1900-2025
    - Ngày hợp lệ (leap years, etc.)
    
    Returns: True nếu valid, False nếu invalid
    """
    if not dob:
        return False
    
    try:
        parsed_date = datetime.strptime(dob, "%Y-%m-%d")
        
        # Check year range (born 1900-2025)
        if parsed_date.year < 1900 or parsed_date.year > 2025:
            return False
        
        return True
    except ValueError:
        return False


# ─── Register ────────────────────────────────────────────────────────────────

def register_user(email, password, fullname, phone, dob):
    """
    [Register] Tạo user mới trong Cognito + DynamoDB profile
    
    Args:
        email (str): Email đăng nhập
        password (str): Mật khẩu (>=8 ký tự, có số, chữ hoa, ký tự đặc biệt)
        fullname (str): Tên người dùng
        phone (str): Số điện thoại (dạng 0901234567 hoặc +84901234567)
        dob (str): Ngày sinh (YYYY-MM-DD)
    
    Returns:
        dict: {
            "success": True,
            "user_id": "...",
            "email": "...",
            "message": "Đăng ký thành công. Vui lòng kiểm tra email để xác thực."
        }
    
    Raises:
        Exception: Lỗi tạo Cognito user hoặc DynamoDB profile
    """
    
    try:
        # ───────────────────────────────────────────────────────────────────
        # [1/3] Validate input
        # ───────────────────────────────────────────────────────────────────
        if not email or '@' not in email:
            raise ValueError("Email không hợp lệ")
        
        if not password or len(password) < 8:
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
        
        # Validate fullname (reject XSS attempts, special chars)
        if not validate_fullname(fullname):
            raise ValueError("Tên người dùng phải từ 2-100 ký tự, không chứa ký tự đặc biệt")
        
        # Validate phone format strictly (no spaces, dashes, parens)
        if not validate_phone_format(phone):
            raise ValueError("Số điện thoại phải là 0901234567 hoặc +84901234567")
        
        # Validate DOB with year range check
        if not validate_dob(dob):
            raise ValueError("Ngày sinh phải theo định dạng YYYY-MM-DD, năm từ 1900-2025")
        
        logger.info(f"[Register] Bắt đầu register email={email}")
        
        # ───────────────────────────────────────────────────────────────────
        # [2/3] Tạo user trong Cognito
        # ───────────────────────────────────────────────────────────────────
        cognito = get_cognito_client()
        
        # Normalize phone to E.164 format
        formatted_phone = normalize_phone(phone)
        
        # SignUp in Cognito (user sẽ nhận email confirmation)
        response = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': fullname},
                {'Name': 'phone_number', 'Value': formatted_phone},
                {'Name': 'birthdate', 'Value': dob},
            ]
        )
        
        user_id = response['UserSub']
        logger.info(f"[Register] ✅ Cognito user created: user_id={user_id}")
        
        # ───────────────────────────────────────────────────────────────────
        # [3/3] Tạo profile trong DynamoDB
        # ───────────────────────────────────────────────────────────────────
        logger.info(f"[Register] [DEBUG] Getting DynamoDB resource...")
        dynamodb = get_dynamodb_resource()
        logger.info(f"[Register] [DEBUG] DynamoDB resource OK")
        
        logger.info(f"[Register] [DEBUG] Getting table: {DYNAMODB_USERS_TABLE}")
        table = dynamodb.Table(DYNAMODB_USERS_TABLE)
        logger.info(f"[Register] [DEBUG] Table object created")
        
        timestamp = get_timestamp()
        # Calculate verification timeout: 5 minutes from now
        verification_pending_until = (datetime.utcnow() + timedelta(minutes=5)).replace(microsecond=0).isoformat() + 'Z'
        
        logger.info(f"[Register] [DEBUG] Calling table.put_item() with user_id={user_id}")
        table.put_item(
            Item={
                'user_id': user_id,
                'email': email,
                'fullname': fullname,
                'phone': formatted_phone,
                'dob': dob,
                'avatar': None,
                'avatar_url': None,
                'created_at': timestamp,
                'updated_at': timestamp,
                # ─────────── EMAIL VERIFICATION (NEW) ─────────────────
                'email_verified': False,  # Mirrors Cognito (not verified yet)
                'verification_pending_until': verification_pending_until,  # Auto-cleanup after 5 min
                'verification_attempts': 0,  # Track resend attempts
                # ─────────── SUBSCRIPTION & QUOTA (NEW) ───────────────
                'subscription_plan': 'free',
                'document_quota': 50,  # Free tier: 50 documents
                'documents_used': 0,
                'storage_quota_gb': 1,  # 1GB free
                # ─────────── PREFERENCES (NEW) ────────────────────────
                'user_preferences': {
                    'language': 'vi',
                    'theme': 'light',
                    'notifications_enabled': True,
                    'timezone': 'Asia/Ho_Chi_Minh',
                },
            }
        )
        logger.info(f"[Register] ✅ DynamoDB profile created: user_id={user_id}")
        logger.info(f"[Register] Verification timeout set to {verification_pending_until}")
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "message": "Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản."
        }
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        logger.error(f"[Register] ❌ Cognito error: {error_code} - {error_msg}")
        
        # Map Cognito errors to user-friendly messages
        if error_code == 'UsernameExistsException':
            raise Exception("Email này đã được đăng ký")
        elif error_code == 'InvalidParameterException':
            # Check if error is related to email already existing
            if 'already' in error_msg.lower() or 'exist' in error_msg.lower():
                raise Exception("Email này đã được đăng ký")
            raise Exception(f"Thông tin không hợp lệ: {error_msg}")
        elif error_code == 'InvalidPasswordException':
            raise Exception("Mật khẩu phải chứa chữ hoa, chữ thường, số và ký tự đặc biệt")
        else:
            raise Exception(f"Lỗi tạo tài khoản: {error_msg}")
    
    except Exception as e:
        logger.error(f"[Register] ❌ Error: {str(e)}")
        raise


# ─── Confirm Email ──────────────────────────────────────────────────────────

def confirm_user_signup(email, confirmation_code):
    """
    [ConfirmSignUp] Xác thực email người dùng
    SYNC PATTERN: Cognito first (source of truth) → DynamoDB second (cache)
    
    Args:
        email (str): Email của user
        confirmation_code (str): Code từ email xác thực
    
    Returns:
        dict: { "success": True, "message": "..." }
    
    Raises:
        Exception: Lỗi xác thực
    """
    
    try:
        logger.info(f"[ConfirmSignUp] Xác thực email={email}")
        
        cognito = get_cognito_client()
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 1: Confirm signup in COGNITO FIRST (Source of Truth)
        # ─────────────────────────────────────────────────────────────────
        try:
            cognito.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,
                ConfirmationCode=confirmation_code
            )
            logger.info(f"[ConfirmSignUp] ✅ Cognito email verified for {email}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            logger.error(f"[ConfirmSignUp] ❌ Cognito error: {error_code} - {error_msg}")
            
            if error_code == 'InvalidParameterException':
                raise Exception("Mã xác thực không hợp lệ hoặc đã hết hạn")
            elif error_code == 'UserNotFoundException':
                raise Exception("Không tìm thấy user")
            else:
                raise Exception(f"Lỗi xác thực: {error_msg}")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 2: Update DYNAMODB (Cache) - Mirror verification status
        # ─────────────────────────────────────────────────────────────────
        try:
            # Get user from Cognito to find user_id
            user = cognito.admin_get_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email
            )
            user_id = user['Username']  # or from user attributes
            
            # Find user_id from sub attribute
            for attr in user.get('UserAttributes', []):
                if attr['Name'] == 'sub':
                    user_id = attr['Value']
                    break
            
            # Update DynamoDB to mirror email_verified and clear timeout
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(DYNAMODB_USERS_TABLE)
            table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET email_verified = :verified, verification_pending_until = :null, updated_at = :now',
                ExpressionAttributeValues={
                    ':verified': True,
                    ':null': None,  # Clear timeout
                    ':now': get_timestamp(),
                }
            )
            logger.info(f"[DynamoDB] ✅ Updated email_verified for {user_id}")
        except Exception as e:
            # Log warning but don't fail - Cognito already confirmed
            logger.warning(f"[DynamoDB] ⚠️ Failed to update verification status: {e}")
        
        return {
            "success": True,
            "message": "Email xác thực thành công! Bạn có thể đăng nhập ngay."
        }
    
    except Exception as e:
        logger.error(f"[ConfirmSignUp] ❌ Error: {str(e)}")
        raise
