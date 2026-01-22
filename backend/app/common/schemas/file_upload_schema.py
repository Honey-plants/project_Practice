from pydantic import BaseModel

class UploadInputResponse(BaseModel):
    upload_type: str
    member_id: int

    # 공통 식별자(local path or s3 key)
    # local / s3 구분 key 값 공통 관리
    file_key: str

    # 개발 단계에서 사용 // 추후 비 노출로 사용 x
    stored_file_name: str
    org_file_name: str
    mime_type: str
    size_bytes: int