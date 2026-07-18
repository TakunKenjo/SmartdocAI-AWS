"""
[SmartDocAI-Auth] auth_service.py
Dịch vụ xác thực: Register, Login, Confirm Code, etc.
Tích hợp Cognito + DynamoDB
"""

import boto3
import logging
import re
from datetime import datetime
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
    - Năm: 1900 đến năm hiện tại (không hard-code số cứng để tránh lỗi
      khi năm hệ thống vượt qua mốc cố định, ví dụ 2025 -> 2026)
    - Ngày hợp lệ (leap years, etc.)
    
    Returns: True nếu valid, False nếu invalid
    """
    if not dob:
        return False
    
    try:
        parsed_date = datetime.strptime(dob, "%Y-%m-%d")
        
        # Check year range (born 1900 -> năm hiện tại)
        current_year = datetime.now().year
        if parsed_date.year < 1900 or parsed_date.year > current_year:
            return False
        
        return True
    except ValueError:
        return False


def has_native_user_with_email(email: str, current_user_id: str) -> bool:
    """
    Kiểm tra email Google có đang trùng với một user Cognito native hay không.
    Native user của pool này dùng email làm Username; Google federated user thường
    có Username dạng "Google_xxx". Nếu tìm thấy native user khác sub thì chặn để
    tránh tạo hai tài khoản app cho cùng một email.
    """
    if not email:
        return False

    cognito = get_cognito_client()
    response = cognito.list_users(
        UserPoolId=COGNITO_USER_POOL_ID,
        Filter=f'email = "{email}"'
    )

    for user in response.get('Users', []):
        attrs = {attr['Name']: attr['Value'] for attr in user.get('Attributes', [])}
        user_id = attrs.get('sub')
        username = user.get('Username', '')

        if user_id != current_user_id and username.lower() == email.lower():
            return True

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
            raise ValueError(f"Ngày sinh phải theo định dạng YYYY-MM-DD, năm từ 1900 đến {datetime.now().year}")
        
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
        
        # LƯU Ý: KHÔNG tạo DynamoDB profile ở đây.
        # Profile chỉ được tạo sau khi user xác thực email thành công (xem confirm_user_signup()).
        # Lý do: user chưa verify thì cũng không login được (Cognito chặn UNCONFIRMED),
        # nên tạo profile sớm chỉ sinh ra rác + cần thêm scheduler dọn dẹp không cần thiết.
        
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
        # STEP 2: Tạo DYNAMODB PROFILE (chỉ tạo ở đây, sau khi verify thành công)
        # ─────────────────────────────────────────────────────────────────
        try:
            # Lấy đầy đủ attributes từ Cognito để tạo profile
            user = cognito.admin_get_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email
            )
            
            attrs = {attr['Name']: attr['Value'] for attr in user.get('UserAttributes', [])}
            user_id = attrs.get('sub', user['Username'])
            
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(DYNAMODB_USERS_TABLE)
            timestamp = get_timestamp()
            
            # put_item với ConditionExpression: chỉ tạo nếu chưa tồn tại (idempotent,
            # tránh trường hợp confirm được gọi lại/duplicate ghi đè profile đã có)
            table.put_item(
                Item={
                    'user_id': user_id,
                    'email': attrs.get('email', email),
                    'fullname': attrs.get('name', ''),
                    'phone': attrs.get('phone_number', ''),
                    'dob': attrs.get('birthdate', ''),
                    'avatar': None,
                    'avatar_url': None,
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    'subscription_plan': 'free',
                    'document_quota': 50,
                    'documents_used': 0,
                    'storage_quota_gb': 1,
                    'user_preferences': {
                        'language': 'vi',
                        'theme': 'light',
                        'notifications_enabled': True,
                        'timezone': 'Asia/Ho_Chi_Minh',
                    },
                },
                ConditionExpression='attribute_not_exists(user_id)'
            )
            logger.info(f"[DynamoDB] ✅ Profile created: user_id={user_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.info(f"[DynamoDB] Profile đã tồn tại, bỏ qua: user_id={user_id}")
            else:
                # Log warning but don't fail - Cognito đã confirm rồi, /api/profile sẽ tự tạo lại (self-healing)
                logger.warning(f"[DynamoDB] ⚠️ Không tạo được profile: {e}")
        except Exception as e:
            logger.warning(f"[DynamoDB] ⚠️ Không tạo được profile: {e}")
        
        return {
            "success": True,
            "message": "Email xác thực thành công! Bạn có thể đăng nhập ngay."
        }
    
    except Exception as e:
        logger.error(f"[ConfirmSignUp] ❌ Error: {str(e)}")
        raise


# ─── Cleanup unconfirmed users (gọi định kỳ bởi EventBridge Scheduled Rule) ────

def cleanup_unconfirmed_users(max_age_minutes: int = 5) -> dict:
    """
    Xóa các user Cognito ở trạng thái UNCONFIRMED đã tồn tại quá `max_age_minutes` phút.
    Không đụng gì tới DynamoDB vì user UNCONFIRMED không có profile ở đó (theo thiết kế
    hiện tại: profile chỉ tạo sau khi confirm-signup thành công).

    Được gọi bởi EventBridge Scheduled Rule (không phải qua HTTP), xem app_api.handler().
    """
    from datetime import timezone, timedelta

    cognito = get_cognito_client()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=max_age_minutes)

    deleted = []
    failed = []

    try:
        paginator = cognito.get_paginator('list_users')
        pages = paginator.paginate(
            UserPoolId=COGNITO_USER_POOL_ID,
            Filter='cognito:user_status = "UNCONFIRMED"'
        )

        for page in pages:
            for user in page.get('Users', []):
                username = user['Username']
                created_at = user['UserCreateDate']

                if created_at < cutoff:
                    try:
                        cognito.admin_delete_user(
                            UserPoolId=COGNITO_USER_POOL_ID,
                            Username=username
                        )
                        deleted.append(username)
                        logger.info(f"[Cleanup] ✅ Đã xóa user UNCONFIRMED quá hạn: {username} (tạo lúc {created_at})")
                    except ClientError as e:
                        failed.append({"username": username, "error": str(e)})
                        logger.error(f"[Cleanup] ❌ Không xóa được {username}: {e}")

    except ClientError as e:
        logger.error(f"[Cleanup] ❌ Lỗi khi list users: {e}")
        raise

    result = {
        "success": True,
        "deleted_count": len(deleted),
        "deleted": deleted,
        "failed_count": len(failed),
        "failed": failed,
    }
    logger.info(f"[Cleanup] Hoàn thành: xóa {len(deleted)} user, lỗi {len(failed)} user")
    return result
