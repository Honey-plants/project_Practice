from backend.app.core import config

# ---------------------------
# Validators
# ---------------------------

# 업로드 타입 화이트리스트 (프론트에서 type 받더라도 서버에서 강제)
# 현재 front에서 form type : menu / review 구분
ALLOWED_UPLOAD_TYPES = {"menu", "review"}

# 이미지 type
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

# 이미지 size
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

# front 에서 받은 type 재 검증
def normalize_upload_type(value: str) -> str:
    t = (value or "").lower().strip()
    if t not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("Invalid upload type")
    return t

# 이미지 size, mime 검증
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
    여기서 local/s3를 '하나로 통일'하는 핵심:
    - STORAGE_DRIVER 값에 따라 같은 인터페이스(save_input/delete_input/download_to)를 가진 구현체를 반환
    """
    # s3 일 때
    if config.STORAGE_DRIVER == "s3":
        from backend.app.common.storage.s3 import S3UploadStorage
        return S3UploadStorage(
            bucket=config.S3_BUCKET,
            region=(config.S3_REGION or None),
            prefix=(config.S3_PREFIX or "upload").strip("/"),
        )

    # local 일 때
    from backend.app.common.storage.local import LocalUploadStorage
    return LocalUploadStorage(upload_root=config.LOCAL_UPLOAD_DIR)