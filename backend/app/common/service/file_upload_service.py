import os
import uuid
from pathlib import Path
from fastapi import UploadFile

from backend.app.common.utils.util import get_storage, normalize_upload_type
from backend.app.common.storage.types import UploadObject

# 추후 S3 DIR 수정 필요!
_WORK_DIR = Path("./_work")
_WORK_DIR.mkdir(parents=True, exist_ok=True)

async def upload_input_file(*, upload_type: str, member_id: int, upload: UploadFile) -> UploadObject:
    """
    업로드 저장: local/s3 동일
    반환 UploadObject.file_key로 이후 처리/삭제 통일
    """
    # receipt / review
    t = normalize_upload_type(upload_type)
    storage = get_storage()
    return await storage.save_input(upload_type=t, member_id=member_id, upload=upload)

def delete_input_file(*, file_key: str) -> None:
    """
    삭제: local(path)/s3(key) 동일 인터페이스
    """
    storage = get_storage()
    storage.delete_input(file_key=file_key)

def ensure_local_path(obj: UploadObject):
    """
    로직이 '파일 경로'를 필요로 할 때 local/s3 통일:
    - local: obj.input_path 그대로 사용
    - s3: file_key(object key)를 다운로드해서 로컬 임시 파일 생성 후 path 반환
    return: (local_path, cleanup_fn)
    """
    storage = get_storage()

    # local은 이미 path 있음
    if obj.input_path:
        return obj.input_path, lambda: None

    # s3는 다운로드 필요
    ext = os.path.splitext(obj.stored_file_name)[1] or ".bin"
    local_path = _WORK_DIR / f"dl_{uuid.uuid4().hex}{ext}"

    if not hasattr(storage, "download_to"):
        raise RuntimeError("Storage does not support download_to()")

    storage.download_to(file_key=obj.file_key, dest_path=str(local_path))

    def cleanup():
        try:
            if local_path.exists():
                local_path.unlink()
        except Exception:
            pass

    return str(local_path), cleanup