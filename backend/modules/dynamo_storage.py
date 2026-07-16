"""
DynamoDB Storage Helper Module cho SmartDocAI
===============================================
Lưu trữ dữ liệu hồ sơ MỞ RỘNG của User — tức những gì Cognito không lưu
(hoặc không tiện lưu) như là attribute chuẩn. Hiện tại chỉ dùng cho avatar_url.

Lưu ý thiết kế:
  - Họ tên / Email / SĐT / Ngày sinh -> đã lưu trực tiếp trong Cognito
    (attribute: name, email, phone_number, birthdate) qua cognitoUser.updateAttributes()
    ở phía Frontend rồi, KHÔNG cần đưa vào DynamoDB nữa (tránh 2 nơi lưu bị lệch dữ liệu).
  - Avatar: ảnh gốc lưu trên S3 (s3://<bucket>/avatars/<user_id>.jpg),
    còn URL trỏ tới ảnh đó thì lưu ở đây (DynamoDB) để tra cứu nhanh mỗi khi cần
    hiển thị avatar (ví dụ ngay sau khi đăng nhập lại).

Bảng: smartdocai-user-profiles
  - Partition Key: user_id (String) — chính là "sub" (Cognito User ID)
  - Attribute:      avatar_url (String)
  - Attribute:      updated_at (String, ISO 8601)
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

import config

logger = logging.getLogger(__name__)

_dynamodb_resource = None


def _get_table():
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb", region_name=config.AWS_DEFAULT_REGION)
    return _dynamodb_resource.Table(config.DYNAMO_TABLE_USER_PROFILES)


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Lấy hồ sơ mở rộng của 1 user. Trả None nếu user chưa từng cập nhật gì (chưa có item)."""
    try:
        response = _get_table().get_item(Key={"user_id": user_id})
        return response.get("Item")
    except ClientError as e:
        logger.error(f"[DynamoDB] Lỗi khi đọc profile của {user_id}: {e}")
        return None


def upsert_avatar_url(user_id: str, avatar_url: str) -> bool:
    """Tạo mới (nếu chưa có) hoặc cập nhật avatar_url cho 1 user."""
    try:
        _get_table().put_item(
            Item={
                "user_id": user_id,
                "avatar_url": avatar_url,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(f"[DynamoDB] Đã cập nhật avatar_url cho user {user_id}")
        return True
    except ClientError as e:
        logger.error(f"[DynamoDB] Lỗi khi lưu avatar_url cho {user_id}: {e}")
        return False
