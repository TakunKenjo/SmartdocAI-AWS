"""
S3 Storage Helper Module cho SmartDocAI
Xử lý tất cả các thao tác đọc/ghi dữ liệu lên Amazon S3.

Cấu trúc S3:
  s3://<bucket>/vectorstore/<index_name>/  - FAISS index files
  s3://<bucket>/metadata/processed_files.json
  s3://<bucket>/metadata/chat_history.json
  s3://<bucket>/metadata/search_config.json
  s3://<bucket>/uploads/<filename>        - uploaded documents
"""

import os
import json
import logging
import shutil
import tempfile
from typing import Optional, Any

import boto3
from botocore.exceptions import ClientError

import config

logger = logging.getLogger(__name__)

# S3 client (dùng IAM Role của Lambda, không cần pass credentials)
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", region_name=config.AWS_DEFAULT_REGION)
    return _s3_client


# ─── JSON Metadata ──────────────────────────────────────────────────────────

def save_json(data: Any, s3_key: str) -> bool:
    """Lưu dict/list dưới dạng JSON lên S3."""
    try:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        get_s3_client().put_object(
            Bucket=config.S3_BUCKET,
            Key=s3_key,
            Body=body,
            ContentType="application/json",
        )
        logger.info(f"[S3] Đã lưu JSON: s3://{config.S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.error(f"[S3] Lỗi khi lưu JSON {s3_key}: {e}")
        return False


def load_json(s3_key: str, default=None) -> Any:
    """Tải JSON từ S3. Trả về default nếu không tồn tại."""
    try:
        response = get_s3_client().get_object(
            Bucket=config.S3_BUCKET, Key=s3_key
        )
        return json.loads(response["Body"].read().decode("utf-8"))
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            logger.info(f"[S3] Chưa có file: {s3_key}")
            return default
        logger.error(f"[S3] Lỗi khi tải JSON {s3_key}: {e}")
        return default
    except Exception as e:
        logger.error(f"[S3] Lỗi khi tải JSON {s3_key}: {e}")
        return default


# ─── File Upload/Download ────────────────────────────────────────────────────

def generate_presigned_upload_url(s3_key: str, content_type: str = "application/octet-stream", expiration: int = 3600) -> Optional[str]:
    """Tạo presigned URL cho phép Frontend upload trực tiếp lên S3 qua HTTP PUT."""
    try:
        url = get_s3_client().generate_presigned_url(
            "put_object",
            Params={
                "Bucket": config.S3_BUCKET,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expiration
        )
        logger.info(f"[S3] Generated Presigned Upload URL cho key: {s3_key}")
        return url
    except Exception as e:
        logger.error(f"[S3] Lỗi khi sinh Presigned URL cho {s3_key}: {e}")
        return None


def upload_file(local_path: str, s3_key: str) -> bool:
    """Upload file từ local lên S3."""
    try:
        get_s3_client().upload_file(local_path, config.S3_BUCKET, s3_key)
        logger.info(f"[S3] Đã upload: {local_path} → s3://{config.S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.error(f"[S3] Lỗi khi upload {local_path}: {e}")
        return False


def download_file(s3_key: str, local_path: str) -> bool:
    """Download file từ S3 về local."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        get_s3_client().download_file(config.S3_BUCKET, s3_key, local_path)
        logger.info(f"[S3] Đã download: s3://{config.S3_BUCKET}/{s3_key} → {local_path}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return False
        logger.error(f"[S3] Lỗi khi download {s3_key}: {e}")
        return False
    except Exception as e:
        logger.error(f"[S3] Lỗi khi download {s3_key}: {e}")
        return False


def key_exists(s3_key: str) -> bool:
    """Kiểm tra xem một S3 key có tồn tại không."""
    try:
        get_s3_client().head_object(Bucket=config.S3_BUCKET, Key=s3_key)
        return True
    except ClientError:
        return False


def list_keys(prefix: str) -> list:
    """Liệt kê tất cả S3 keys có prefix nhất định."""
    try:
        response = get_s3_client().list_objects_v2(
            Bucket=config.S3_BUCKET, Prefix=prefix
        )
        return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception as e:
        logger.error(f"[S3] Lỗi khi list keys {prefix}: {e}")
        return []


def delete_key(s3_key: str) -> bool:
    """Xóa một key trên S3."""
    try:
        get_s3_client().delete_object(Bucket=config.S3_BUCKET, Key=s3_key)
        logger.info(f"[S3] Đã xóa: s3://{config.S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.error(f"[S3] Lỗi khi xóa {s3_key}: {e}")
        return False


def delete_prefix(prefix: str) -> bool:
    """Xóa tất cả objects có chung prefix (xóa thư mục)."""
    try:
        keys = list_keys(prefix)
        if not keys:
            return True
        objects = [{"Key": k} for k in keys]
        get_s3_client().delete_objects(
            Bucket=config.S3_BUCKET,
            Delete={"Objects": objects},
        )
        logger.info(f"[S3] Đã xóa {len(objects)} objects với prefix: {prefix}")
        return True
    except Exception as e:
        logger.error(f"[S3] Lỗi khi xóa prefix {prefix}: {e}")
        return False


# ─── FAISS Vector Store Sync ─────────────────────────────────────────────────

def upload_vectorstore(local_dir: str, index_name: str) -> bool:
    """
    Upload toàn bộ thư mục FAISS index lên S3.
    FAISS lưu 2 files: index.faiss và index.pkl
    """
    s3_prefix = f"{config.S3_VECTORSTORE_PREFIX}/{index_name}/"
    success = True

    for filename in os.listdir(local_dir):
        local_path = os.path.join(local_dir, filename)
        if os.path.isfile(local_path):
            s3_key = s3_prefix + filename
            if not upload_file(local_path, s3_key):
                success = False

    if success:
        logger.info(f"[S3] Vector store đã được sync lên S3: {s3_prefix}")
    return success


def download_vectorstore(local_dir: str, index_name: str) -> bool:
    """
    Download FAISS index từ S3 về /tmp.
    Trả về True nếu tồn tại và download thành công.
    """
    s3_prefix = f"{config.S3_VECTORSTORE_PREFIX}/{index_name}/"
    keys = list_keys(s3_prefix)

    if not keys:
        logger.info(f"[S3] Chưa có vector store trên S3: {s3_prefix}")
        return False

    os.makedirs(local_dir, exist_ok=True)

    for s3_key in keys:
        filename = os.path.basename(s3_key)
        local_path = os.path.join(local_dir, filename)
        if not download_file(s3_key, local_path):
            return False

    logger.info(f"[S3] Vector store đã được tải về: {local_dir}")
    return True


def delete_vectorstore(index_name: str) -> bool:
    """Xóa FAISS index trên S3."""
    s3_prefix = f"{config.S3_VECTORSTORE_PREFIX}/{index_name}/"
    return delete_prefix(s3_prefix)
