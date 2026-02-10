# file_upload_schema.py
from pydantic import BaseModel

class UploadInputResponse(BaseModel):
    upload_type: str
    member_id: int

    file_key: str
    stored_file_name: str
    org_file_name: str
    mime_type: str
    size_bytes: int


class MenuUploadResponse(UploadInputResponse):
    # pipeline run info
    run_id: str
    run_dir: str

    # filesystem paths (디버깅/로그용)
    rectified_path: str
    translate_json_path: str

    # 프론트가 실제로 접근할 URL (중요)
    rectified_url: str
    translate_json_url: str
