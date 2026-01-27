from typing import Optional
from pydantic import BaseModel

class UploadInputResponse(BaseModel):
    upload_type: str
    member_id: int
    file_key: str
    stored_file_name: str
    org_file_name: str
    mime_type: str
    size_bytes: int

    # 추가: 메뉴 파이프라인 결과 추적용
    run_id: Optional[str] = None
    rectified_path: Optional[str] = None
    final_json_path: Optional[str] = None
