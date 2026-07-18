"""
Cognito Auth Helper Module cho SmartDocAI
==========================================
Xác thực JWT Token (ID Token) do AWS Cognito cấp cho các API động chạm tới
dữ liệu riêng tư của user (ví dụ: cập nhật avatar, đọc hồ sơ cá nhân).

Cách hoạt động:
  1. Frontend (axiosConfig.js) tự động đính kèm header:
         Authorization: Bearer <id_token>
  2. Backend tải bộ public keys (JWKS) của User Pool từ Cognito
     (thư viện PyJWT tự cache lại nên không phải gọi lại mỗi request).
  3. Verify chữ ký (RS256), hạn dùng (exp), issuer (iss), audience (aud = Client ID).
  4. Nếu hợp lệ -> trả về payload token, trong đó payload["sub"] chính là
     Cognito User ID (userId) — dùng để đối chiếu quyền sở hữu dữ liệu.

Cài đặt thêm: pip install "PyJWT[crypto]"
"""

import logging

import jwt
from jwt import PyJWKClient
from fastapi import Header, HTTPException

import config

logger = logging.getLogger(__name__)

_JWKS_URL = (
    f"https://cognito-idp.{config.AWS_DEFAULT_REGION}.amazonaws.com/"
    f"{config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)
_ISSUER = (
    f"https://cognito-idp.{config.AWS_DEFAULT_REGION}.amazonaws.com/"
    f"{config.COGNITO_USER_POOL_ID}"
)

# PyJWKClient tự cache các public key bên trong, không cần tự viết cache riêng
_jwk_client = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(_JWKS_URL)
    return _jwk_client


def decode_token(token: str) -> dict:
    """Giải mã + xác thực chữ ký của Cognito ID Token. Raise HTTPException nếu không hợp lệ."""
    try:
        signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config.COGNITO_APP_CLIENT_ID,
            issuer=_ISSUER,
            options={"require": ["exp", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token đã hết hạn. Vui lòng đăng nhập lại.")
    except jwt.PyJWTError as e:
        logger.warning(f"[Auth] Token không hợp lệ: {e}")
        raise HTTPException(status_code=401, detail="Token không hợp lệ.")


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    FastAPI Dependency — dùng trong route như sau:

        @app.put("/api/profile/avatar")
        def update_avatar(data: AvatarUpdateRequest,
                           current_user: dict = Depends(cognito_auth.get_current_user)):
            user_id = current_user["sub"]  # Cognito User ID đã được xác thực

    Trả về payload token (dict). Raise 401 nếu thiếu/sai token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Thiếu Authorization Bearer Token.")
    token = authorization.split(" ", 1)[1].strip()
    return decode_token(token)
