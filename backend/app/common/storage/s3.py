import os
import uuid
from fastapi import UploadFile

from backend.app.common.utils.util import validate_image
from backend.app.common.storage.types import UploadObject

try:
    import boto3
except Exception:
    boto3 = None

def _ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

class S3UploadStorage:
    def __init__(self, bucket: str, prefix: str = "upload", region: str | None = None):
        if boto3 is None:
            raise RuntimeError("boto3 is required for S3 storage")
        if not bucket:
            raise RuntimeError("S3_BUCKET is required when STORAGE_DRIVER=s3")

        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = boto3.client("s3", region_name=region)

    async def save_input(self, *, upload_type: str, member_id: int, upload: UploadFile) -> UploadObject:
        org_name = upload.filename or "unknown"
        mime = upload.content_type or "application/octet-stream"

        data = await upload.read()
        size = len(data)
        validate_image(mime, size)

        ext = _ext(org_name)
        stored_name = f"input_{upload_type}_{uuid.uuid4().hex}{ext}"
        key = f"{self.prefix}/{upload_type}/{member_id}/{stored_name}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=mime,
        )

        # s3: 공통 식별자 file_key = s3 key
        return UploadObject(
            upload_type=upload_type,
            member_id=member_id,
            file_key=key,
            input_path=None,
            org_file_name=org_name,
            stored_file_name=stored_name,
            mime_type=mime,
            size_bytes=size,
        )

    def delete_input(self, *, file_key: str) -> None:
        # s3: file_key는 object key
        self.client.delete_object(Bucket=self.bucket, Key=file_key)

    def is_local(self) -> bool:
        return False

    def download_to(self, *, file_key: str, dest_path: str) -> None:
        # 로직이 파일 경로를 요구할 때 사용
        self.client.download_file(self.bucket, file_key, dest_path)