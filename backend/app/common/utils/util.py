import os
from backend.app.core import config

# ---------------------------
# Validators
# ---------------------------

ALLOWED_UPLOAD_TYPES = {"menu", "receipt"}  # 이번 로직에 맞춰 최소만
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def normalize_upload_type(value: str) -> str:
    t = (value or "").lower().strip()
    if t not in ALLOWED_UPLOAD_TYPES:
        raise ValueError(f"Invalid upload type: {t}")
    return t


def validate_image(mime_type: str, size_bytes: int) -> None:
    if mime_type not in ALLOWED_MIME:
        raise ValueError(f"Unsupported mime_type: {mime_type}")
    if size_bytes > MAX_SIZE_BYTES:
        raise ValueError(f"File too large: {size_bytes} bytes")


# ---------------------------
# Storage factory (local/s3 통합 관리)
# ---------------------------

def get_storage():
    """
    config의 변수명 체계에 맞춘 공통 storage factory
    """
    if config.STORAGE_BACKEND == "s3":
        from backend.app.common.storage.s3 import S3UploadStorage
        return S3UploadStorage(
            bucket=config.S3_BUCKET,
            prefix_tmp=config.S3_PREFIX_TMP,
            prefix_perm=config.S3_PREFIX_PERM,
            base_prefix="upload",   # S3 상단 폴더(고정)
            region=os.getenv("S3_REGION") if hasattr(__import__("os"), "getenv") else None,
        )

    from backend.app.common.storage.local import LocalUploadStorage
    return LocalUploadStorage(
        upload_root=config.LOCAL_UPLOAD_ROOT,
        tmp_root=config.LOCAL_TMP_ROOT,
        perm_root=config.LOCAL_PERM_ROOT,
    )
