from dataclasses import dataclass
from typing import Optional

@dataclass
class UploadObject:
    upload_type: str
    member_id: int

    # 공통 식별자 :: local/s3 공통 사용 하기 때문에
    # local: file_key == 로컬 파일 path
    # s3:    file_key == S3 object key
    file_key: str

    # local에서만 의미 있음 (s3는 None) // 추후 s3 사용시 삭제 예정
    input_path: Optional[str]

    org_file_name: str
    stored_file_name: str
    mime_type: str
    size_bytes: int