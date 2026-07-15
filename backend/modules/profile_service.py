"""
SmartDocAI - Profile Service
Quản lý hồ sơ người dùng: thông tin cá nhân, avatar, đổi mật khẩu
Tương tác với DynamoDB (smartdocai-user-profiles) và Cognito User Pool
"""

import os
import logging
import json
import time
import base64
import re
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

import config

logger = logging.getLogger(__name__)

# DynamoDB clients
_dynamodb_client = None
_dynamodb_resource = None

USERS_TABLE = "smartdocai-user-profiles"
COGNITO_USERPOOL_ID = os.getenv("COGNITO_USERPOOL_ID", "us-east-1_3oq5wIiuu")


def get_dynamodb_client():
    """Lấy DynamoDB client singleton"""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client("dynamodb", region_name=config.AWS_DEFAULT_REGION)
    return _dynamodb_client


def get_dynamodb_resource():
    """Lấy DynamoDB resource singleton"""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb", region_name=config.AWS_DEFAULT_REGION)
    return _dynamodb_resource


def get_cognito_client():
    """Lấy Cognito client"""
    return boto3.client("cognito-idp", region_name=config.AWS_DEFAULT_REGION)


# ─── Helper Functions ───────────────────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """
    Chuẩn hóa số điện thoại sang E.164 format
    Ví dụ: 0901234567 → +84901234567
    """
    if not phone:
        return ""
    
    phone = phone.strip().replace(" ", "")
    
    # Thay 0 đầu bằng +84 (Việt Nam)
    if phone.startswith("0"):
        phone = "+84" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+84" + phone
    
    return phone


def get_timestamp() -> int:
    """Lấy Unix timestamp hiện tại"""
    return int(time.time())


def item_to_dict(dynamodb_item: Dict) -> Dict:
    """Convert DynamoDB item (Decimal) sang Python dict bình thường"""
    if not dynamodb_item:
        return {}
    
    result = {}
    for key, value in dynamodb_item.items():
        if isinstance(value, Decimal):
            result[key] = int(value) if value % 1 == 0 else float(value)
        elif isinstance(value, dict) and "NULL" in value:
            result[key] = None
        else:
            result[key] = value
    
    return result


# ─── Profile Operations ────────────────────────────────────────────────────

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy hồ sơ người dùng từ DynamoDB
    
    Args:
        user_id: Cognito sub (user ID)
    
    Returns:
        Dict user profile hoặc None nếu không tìm thấy
    """
    try:
        table = get_dynamodb_resource().Table(USERS_TABLE)
        response = table.get_item(Key={"user_id": user_id})
        
        if "Item" not in response:
            logger.warning(f"User không tìm thấy: {user_id}")
            return None
        
        user = item_to_dict(response["Item"])
        logger.info(f"[DynamoDB] Lấy profile: {user_id}")
        return user
        
    except ClientError as e:
        logger.error(f"[DynamoDB] Lỗi lấy profile {user_id}: {e}")


def ensure_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Đảm bảo user profile tồn tại trong DynamoDB.
    Nếu không tồn tại, tự động tạo profile mới với thông tin mặc định.
    
    Args:
        user_id: Cognito sub
    
    Returns:
        User profile (existing hoặc newly created)
    """
    try:
        # Try to get existing profile
        existing = get_user_profile(user_id)
        if existing:
            return existing
        
        # Create new profile with defaults
        logger.info(f"[DynamoDB] Tạo profile mới: {user_id}")
        
        table = get_dynamodb_resource().Table(USERS_TABLE)
        now = datetime.utcnow().isoformat() + "Z"
        
        new_profile = {
            "user_id": user_id,
            "email": "",
            "fullname": "",
            "phone": "",
            "dob": "",
            "avatar_url": None,
            "created_at": now,
            "updated_at": now,
        }
        
        table.put_item(Item=new_profile)
        logger.info(f"[DynamoDB] Profile được tạo: {user_id}")
        return new_profile
        
    except ClientError as e:
        logger.error(f"[DynamoDB] Lỗi tạo profile {user_id}: {e}")
        raise Exception(f"Không thể tạo profile: {e}")
        raise Exception(f"Không thể lấy profile: {e.response['Error']['Message']}")


def create_or_update_profile(user_id: str, email: str, **kwargs) -> Dict[str, Any]:
    """
    Tạo hoặc cập nhật hồ sơ người dùng trong DynamoDB
    
    Args:
        user_id: Cognito sub
        email: Email người dùng
        **kwargs: fullname, phone, dob, avatar, avatar_url, ...
    
    Returns:
        User profile đã cập nhật
    """
    try:
        table = get_dynamodb_resource().Table(USERS_TABLE)
        
        # Chuẩn hóa phone nếu có
        if "phone" in kwargs:
            kwargs["phone"] = normalize_phone(kwargs["phone"])
        
        now = get_timestamp()
        
        # Kiểm tra user cũ để xác định nên tạo mới hay update
        existing = get_user_profile(user_id)
        
        # Tạo mới nếu chưa tồn tại
        if not existing:
            update_data = {
                "user_id": user_id,
                "email": email,
                "created_at": now,
                "updated_at": now,
            }
            # Thêm trường optional cho profile mới
            for key in ["fullname", "phone", "dob", "avatar", "avatar_url"]:
                if key in kwargs and kwargs[key]:
                    update_data[key] = kwargs[key]
            
            table.put_item(Item=update_data)
            logger.info(f"[DynamoDB] Tạo profile mới: {user_id}")
            return update_data
        
        # Update profile hiện tại (dùng update_item để giữ lại các field cũ)
        update_expression_parts = []
        expr_attr_values = {}
        
        # Luôn update email và updated_at
        update_expression_parts.append("email = :email")
        update_expression_parts.append("updated_at = :updated_at")
        expr_attr_values[":email"] = email
        expr_attr_values[":updated_at"] = now
        
        # Cập nhật các field được truyền vào
        for key in ["fullname", "phone", "dob", "avatar", "avatar_url"]:
            if key in kwargs:
                if kwargs[key]:  # Nếu có giá trị thì update
                    update_expression_parts.append(f"{key} = :{key}")
                    expr_attr_values[f":{key}"] = kwargs[key]
                # Nếu giá trị rỗng, không xóa field cũ, chỉ bỏ qua
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        
        logger.info(f"[DynamoDB] Cập nhật profile: {user_id}")
        return response.get("Attributes", {})
        
    except ClientError as e:
        logger.error(f"[DynamoDB] Lỗi cập nhật profile {user_id}: {e}")
        raise Exception(f"Không thể cập nhật profile: {e.response['Error']['Message']}")


def update_personal_info(
    user_id: str,
    fullname: str,
    email: str,
    phone: str,
    dob: str
) -> Dict[str, Any]:
    """
    Cập nhật thông tin cá nhân (name, email, phone, dob)
    SYNC PATTERN: Cognito first (source of truth) → DynamoDB second (cache)
    
    Args:
        user_id: Cognito sub
        fullname: Họ tên
        email: Email
        phone: Số điện thoại
        dob: Ngày sinh (YYYY-MM-DD)
    
    Returns:
        Updated profile
    
    Raises:
        Exception: Nếu Cognito update fail
    """
    try:
        # ─────────────────────────────────────────────────────────────────
        # VALIDATION
        # ─────────────────────────────────────────────────────────────────
        if not fullname or not fullname.strip():
            raise ValueError("Họ tên không được để trống")
        if not email or not email.strip():
            raise ValueError("Email không được để trống")
        if not phone or not phone.strip():
            raise ValueError("Số điện thoại không được để trống")
        if not dob or not dob.strip():
            raise ValueError("Ngày sinh không được để trống")
        
        # Validate email format
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            raise ValueError("Email không hợp lệ")
        
        # Validate phone format (sau khi chuẩn hóa)
        phone_normalized = normalize_phone(phone)
        if not re.match(r"^\+\d{10,15}$", phone_normalized):
            raise ValueError("Số điện thoại không hợp lệ")
        
        # Validate DOB format
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", dob):
            raise ValueError("Ngày sinh phải có định dạng YYYY-MM-DD")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 1: Update COGNITO FIRST (Source of Truth)
        # ─────────────────────────────────────────────────────────────────
        try:
            cognito = get_cognito_client()
            cognito.admin_update_user_attributes(
                UserPoolId=COGNITO_USERPOOL_ID,
                Username=user_id,
                UserAttributes=[
                    {"Name": "name", "Value": fullname},
                    {"Name": "email", "Value": email},
                    {"Name": "phone_number", "Value": phone_normalized},
                    {"Name": "birthdate", "Value": dob},
                ]
            )
            logger.info(f"[Cognito] ✅ Updated attributes for {user_id}")
        except ClientError as e:
            # FAIL IMMEDIATELY - don't touch DynamoDB if Cognito fails
            logger.error(f"[Cognito] ❌ Failed to update: {e}")
            raise Exception(f"Không thể cập nhật thông tin Cognito: {str(e)}")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 2: Update DYNAMODB (Cache) - Eventual Consistency
        # ─────────────────────────────────────────────────────────────────
        try:
            updated_profile = create_or_update_profile(
                user_id=user_id,
                email=email,
                fullname=fullname,
                phone=phone_normalized,
                dob=dob
            )
            logger.info(f"[DynamoDB] ✅ Updated profile for {user_id}")
        except Exception as e:
            # LOG WARNING but don't fail - Cognito already updated
            # Next read will eventually sync
            logger.warning(f"[DynamoDB] ⚠️ Cache sync failed (Cognito already updated): {e}")
        
        return {
            "success": True,
            "user_id": user_id,
            "fullname": fullname,
            "email": email,
            "phone": phone_normalized,
            "dob": dob,
            "sync_status": "cognito_primary"
        }
        
    except ValueError as e:
        logger.error(f"[Validation] {e}")
        raise Exception(str(e))
    except Exception as e:
        logger.error(f"[Profile] Lỗi update personal info {user_id}: {e}")
        raise


def update_avatar(user_id: str, avatar_base64: str, max_size_mb: int = 5) -> Dict[str, Any]:
    """
    Cập nhật avatar người dùng
    - Nếu < 300KB: lưu base64 trực tiếp vào DynamoDB
    - Nếu > 300KB: lưu vào S3, trả về URL
    
    Args:
        user_id: Cognito sub
        avatar_base64: Base64 string (hoặc "data:image/jpeg;base64,...")
        max_size_mb: Kích thước tối đa (MB)
    
    Returns:
        Success response với avatar (base64 hay URL tùy theo size)
    """
    try:
        if not avatar_base64:
            raise ValueError("Avatar không được để trống")
        
        # Parse data URI nếu có
        avatar_data = avatar_base64
        if avatar_base64.startswith("data:"):
            try:
                _, avatar_data = avatar_base64.split(",", 1)
            except ValueError:
                raise ValueError("Avatar format không hợp lệ")
        
        # Decode và check kích thước
        try:
            avatar_bytes = base64.b64decode(avatar_data)
        except Exception as e:
            raise ValueError(f"Base64 decode thất bại: {e}")
        
        size_mb = len(avatar_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"Ảnh quá lớn ({size_mb:.1f}MB), tối đa {max_size_mb}MB")
        
        # Lấy profile hiện tại để giữ lại email và các field khác
        existing_profile = get_user_profile(user_id)
        existing_email = existing_profile.get("email", "") if existing_profile else ""
        
        # Option 1: Lưu base64 trực tiếp vào DynamoDB (< 300KB)
        if size_mb < 0.3:
            updated_profile = create_or_update_profile(
                user_id=user_id,
                email=existing_email,
                avatar=avatar_base64
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "avatar": avatar_base64,
                "storage": "dynamodb",
            }
        
        # Option 2: Lưu vào S3 (> 300KB)
        else:
            import uuid
            avatar_key = f"avatars/{user_id}/{uuid.uuid4().hex}.jpg"
            
            # Upload to S3
            s3_client = boto3.client("s3", region_name=config.AWS_DEFAULT_REGION)
            s3_client.put_object(
                Bucket=config.S3_BUCKET,
                Key=avatar_key,
                Body=avatar_bytes,
                ContentType="image/jpeg",
            )
            
            avatar_url = f"https://{config.S3_BUCKET}.s3.{config.AWS_DEFAULT_REGION}.amazonaws.com/{avatar_key}"
            
            # Lưu URL vào DynamoDB (clear avatar base64 nếu có)
            table = get_dynamodb_resource().Table(USERS_TABLE)
            table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET avatar_url = :url, updated_at = :now REMOVE avatar",
                ExpressionAttributeValues={
                    ":url": avatar_url,
                    ":now": get_timestamp(),
                }
            )
            
            logger.info(f"[S3] Avatar lưu: {avatar_key}")
            
            return {
                "success": True,
                "user_id": user_id,
                "avatar_url": avatar_url,
                "storage": "s3",
            }
        
    except ValueError as e:
        logger.error(f"[Validation] {e}")
        raise Exception(str(e))
    except Exception as e:
        logger.error(f"[Profile] Lỗi update avatar {user_id}: {e}")
        raise


def change_password(
    user_id: str,
    email: str,
    current_password: str,
    new_password: str
) -> Dict[str, Any]:
    """
    Đổi mật khẩu người dùng qua Cognito AdminSetUserPassword
    
    Args:
        user_id: Cognito sub
        email: Email (dùng làm Username cho admin_set_user_password)
        current_password: Mật khẩu hiện tại (gửi lên nhưng không dùng)
        new_password: Mật khẩu mới
    
    Returns:
        Success response
    """
    try:
        if not current_password or not new_password:
            raise ValueError("Mật khẩu không được để trống")
        
        if len(new_password) < 6:
            raise ValueError("Mật khẩu mới phải có ít nhất 6 ký tự")
        
        # Đảm bảo user profile tồn tại trong DynamoDB (tự động tạo nếu cần)
        user_profile = ensure_user_profile(user_id)
        if not user_profile:
            raise ValueError("Không thể tạo/lấy user profile")
        
        # Set mật khẩu mới qua Cognito admin API (dùng email làm username)
        cognito = get_cognito_client()
        cognito.admin_set_user_password(
            UserPoolId=COGNITO_USERPOOL_ID,
            Username=email if email else user_id,  # Ưu tiên email
            Password=new_password,
            Permanent=True
        )
        
        logger.info(f"[Cognito] Đổi mật khẩu: {user_id} ({email})")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "Đổi mật khẩu thành công",
        }
        
    except ValueError as e:
        logger.error(f"[Validation] {e}")
        raise Exception(str(e))
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UserNotFoundException":
            raise Exception("Người dùng không tồn tại")
        elif error_code == "InvalidPasswordException":
            raise Exception("Mật khẩu không đáp ứng yêu cầu độ phức tạp")
        else:
            logger.error(f"[Cognito] Lỗi: {e}")
            raise Exception(f"Lỗi đổi mật khẩu: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"[Profile] Lỗi change password {user_id}: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL VERIFICATION TIMEOUT - Auto-cleanup unverified users
# ═══════════════════════════════════════════════════════════════════════════════

def cleanup_unverified_users() -> Dict[str, Any]:
    """
    BACKGROUND JOB: Xóa tài khoản chưa xác thực email sau khi timeout 5 phút
    
    Logic:
    1. Scan DynamoDB cho users với: verification_pending_until < now AND email_verified = false
    2. Xóa từ Cognito FIRST (nếu không có user, skip)
    3. Xóa từ DynamoDB
    4. Xóa S3 data (nếu có)
    
    Returns:
        dict: {
            "cleaned": int,     # số user bị xóa
            "failed": int,      # số lỗi
            "details": [...]    # chi tiết từng user
        }
    
    Note: Được gọi bởi:
    - Lambda trigger mỗi 1 phút (CloudWatch Events)
    - Hoặc background task trong FastAPI
    - Hoặc manual admin endpoint
    """
    
    try:
        logger.info("[Cleanup] Bắt đầu cleanup unverified users")
        
        now = datetime.utcnow()
        cleaned_count = 0
        failed_count = 0
        details = []
        
        # ─────────────────────────────────────────────────────────────────
        # SCAN DynamoDB: Tìm users hết timeout
        # ─────────────────────────────────────────────────────────────────
        table = get_dynamodb_resource().Table(USERS_TABLE)
        
        # Query pattern: email_verified = false AND verification_pending_until < now
        # Note: Cần có GSI trên (email_verified, verification_pending_until) để efficient
        # Fallback: Scan all + filter in code
        response = table.scan(
            FilterExpression="email_verified = :false AND attribute_exists(verification_pending_until) AND verification_pending_until < :now",
            ExpressionAttributeValues={
                ":false": False,
                ":now": now.isoformat() + 'Z',  # ISO format
            }
        )
        
        unverified_users = response.get('Items', [])
        logger.info(f"[Cleanup] Tìm thấy {len(unverified_users)} users chưa xác thực hết timeout")
        
        cognito = get_cognito_client()
        
        # ─────────────────────────────────────────────────────────────────
        # Xóa từng user: Cognito FIRST → DynamoDB → S3
        # ─────────────────────────────────────────────────────────────────
        for user_data in unverified_users:
            user_id = user_data.get('user_id')
            email = user_data.get('email')
            timeout_at = user_data.get('verification_pending_until')
            
            try:
                # STEP 1: Xóa từ Cognito (Source of Truth)
                try:
                    cognito.admin_delete_user(
                        UserPoolId=COGNITO_USERPOOL_ID,
                        Username=email
                    )
                    logger.info(f"[Cognito] ✅ Deleted unverified user: {user_id} ({email})")
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'UserNotFoundException':
                        logger.warning(f"[Cognito] ⚠️ User not found: {email} (may have been deleted)")
                    else:
                        raise e
                
                # STEP 2: Xóa từ DynamoDB
                table.delete_item(Key={'user_id': user_id})
                logger.info(f"[DynamoDB] ✅ Deleted profile: {user_id}")
                
                # STEP 3: Xóa S3 data (chat history, documents, uploads)
                try:
                    import boto3
                    s3 = boto3.client('s3', region_name=config.AWS_DEFAULT_REGION)
                    
                    # Delete all user data from S3
                    # - s3://smartdocai-storage.../chat_history/{user_id}.json
                    # - s3://smartdocai-storage.../processed_files/{user_id}.json
                    # - s3://smartdocai-storage.../avatars/{user_id}/...
                    # - s3://smartdocai-storage.../uploads/{user_id}/...
                    
                    keys_to_delete = [
                        f'chat_history/{user_id}.json',
                        f'processed_files/{user_id}.json',
                    ]
                    
                    for key in keys_to_delete:
                        try:
                            s3.delete_object(Bucket=config.S3_BUCKET, Key=key)
                            logger.info(f"[S3] ✅ Deleted: {key}")
                        except Exception as e:
                            logger.warning(f"[S3] ⚠️ Failed to delete {key}: {e}")
                    
                    # List and delete all user directory contents (avatars, uploads, etc)
                    try:
                        paginator = s3.get_paginator('list_objects_v2')
                        for prefix in [f'avatars/{user_id}/', f'uploads/{user_id}/']:
                            for page in paginator.paginate(Bucket=config.S3_BUCKET, Prefix=prefix):
                                if 'Contents' in page:
                                    for obj in page['Contents']:
                                        s3.delete_object(Bucket=config.S3_BUCKET, Key=obj['Key'])
                                        logger.info(f"[S3] ✅ Deleted: {obj['Key']}")
                    except Exception as e:
                        logger.warning(f"[S3] ⚠️ Failed to delete user directories: {e}")
                
                except Exception as e:
                    logger.warning(f"[S3] ⚠️ S3 cleanup error for {user_id}: {e}")
                
                cleaned_count += 1
                details.append({
                    "user_id": user_id,
                    "email": email,
                    "timeout_at": timeout_at,
                    "status": "deleted",
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(f"[Cleanup] ❌ Failed to delete user {user_id}: {e}")
                details.append({
                    "user_id": user_id,
                    "email": email,
                    "status": "failed",
                    "error": str(e),
                })
        
        result = {
            "success": True,
            "cleaned": cleaned_count,
            "failed": failed_count,
            "total": len(unverified_users),
            "timestamp": now.isoformat(),
            "details": details,
        }
        
        logger.info(f"[Cleanup] ✅ Hoàn thành: cleaned={cleaned_count}, failed={failed_count}")
        return result
        
    except Exception as e:
        logger.error(f"[Cleanup] ❌ Fatal error: {e}")
        raise


def schedule_cleanup_unverified_users():
    """
    Helper: Schedule cleanup job (được gọi bởi FastAPI startup)
    Có thể dùng APScheduler hoặc background tasks
    
    Usage:
        # In FastAPI startup
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(schedule_cleanup_unverified_users, 'interval', minutes=1)
        scheduler.start()
    """
    try:
        cleanup_unverified_users()
    except Exception as e:
        logger.error(f"[Cleanup] Scheduled task error: {e}")
