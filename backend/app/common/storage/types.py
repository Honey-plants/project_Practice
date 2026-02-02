from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadObject:
    upload_type: str
    member_id: int

    # local: file_key == 로컬 파일 path
    # s3:    file_key == S3 object key
    file_key: str

    # local에서만 의미 있음 (AI는 local path 필요)
    input_path: Optional[str]

    org_file_name: str
    stored_file_name: str
    mime_type: str
    size_bytes: int

    # temp 삭제를 "폴더 단위"로 하려면 prefix_key가 필요함
    # local: 디렉터리 경로 / s3: prefix
    prefix_key: str


@dataclass
class StoredAsset:
    """영구 저장 파일(리뷰 이미지 등)"""

    owner_type: str
    owner_id: int
    member_id: int

    # local: file_key == 로컬 파일 path
    # s3:    file_key == S3 object key
    file_key: str

    # local: "/static/..." 형태 (StaticFiles mount 기준)
    # s3: object key 또는 CDN URL
    storage_path: str

    stored_file_name: str
    org_file_name: str
    mime_type: str
    size_bytes: int
    sort_order: int
