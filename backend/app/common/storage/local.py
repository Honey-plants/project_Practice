import os
import uuid
from pathlib import Path
from fastapi import UploadFile

from backend.app.common.utils.util import validate_image
from backend.app.common.storage.types import UploadObject


def _ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


class LocalUploadStorage:
    def __init__(self, upload_root: Path):
        self.upload_root = Path(upload_root)
        self.upload_root.mkdir(parents=True, exist_ok=True)

    async def save_input(self, *, upload_type: str, member_id: int, upload: UploadFile) -> UploadObject:
        org_name = upload.filename or "unknown"
        mime = upload.content_type or "application/octet-stream"

        data = await upload.read()
        size = len(data)
        validate_image(mime, size)

        ext = _ext(org_name)

        # scoped_dir = self.upload_root / upload_type
        scoped_dir = self.upload_root / upload_type / str(member_id)
        scoped_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"input_{upload_type}_{uuid.uuid4().hex}{ext}"
        path = scoped_dir / stored_name

        with open(path, "wb") as f:
            f.write(data)

        # local: 공통 식별자 file_key = path
        return UploadObject(
            upload_type=upload_type,
            member_id=member_id,
            file_key=str(path),
            input_path=str(path),
            org_file_name=org_name,
            stored_file_name=stored_name,
            mime_type=mime,
            size_bytes=size,
        )

    def delete_input(self, *, file_key: str) -> None:
        """
        file_key == 로컬 파일 경로
        1) 파일 삭제
        2) parent(member_id 폴더) 비었으면 삭제
        3) (옵션) 상위 type 폴더도 비었으면 삭제
        """
        p = Path(file_key)

        # 1) 파일 삭제
        if p.exists() and p.is_file():
            try:
                p.unlink()
            except Exception:
                return

        # 2) member_id 폴더 정리 (upload/{type}/{member_id})
        member_dir = p.parent
        if member_dir.exists() and member_dir.is_dir():
            try:
                # 비었으면 삭제
                if not any(member_dir.iterdir()):
                    member_dir.rmdir()
            except Exception:
                pass

    # local 체크
    def is_local(self) -> bool:
        return True