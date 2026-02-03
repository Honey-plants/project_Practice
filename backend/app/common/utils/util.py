import os
from backend.app.core import config
import json
from typing import Any
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

def ensure_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def dumps_json(v):
    if v is None:
        return None
    if v == [] or v == {}:
        return None
    return json.dumps(v, ensure_ascii=False)


def parse_ids(raw: Any) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw]

    s = str(raw).strip()
    if not s:
        return []

    # JSON 문자열이면 JSON으로 먼저 파싱
    if s.startswith("[") and s.endswith("]"):
        try:
            arr = json.loads(s)
            if isinstance(arr, list):
                return [int(x) for x in arr]
        except Exception:
            pass

    # fallback: "1,2,3" 같은 CSV
    out = []
    for p in s.split(","):
        p = p.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out