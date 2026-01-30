from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from backend.app.core.security.deps import get_current_member
from backend.app.common.service.file_upload_service import (
    upload_input_file, ensure_local_path, delete_input_file
)
from backend.app.features.menu.service import run_menu_model
from backend.app.features.menu.schemas import MenuAnalyzeResponse

router = APIRouter(prefix="/menu", tags=["menu"])

@router.post("/upload", response_model=MenuAnalyzeResponse)
async def menu_upload(
    type: str = Form("menu"),
    file: UploadFile = File(...),
    current=Depends(get_current_member),
):
    obj = await upload_input_file(upload_type=type, member_id=current.member_id, upload=file)
    cleanup_download = lambda: None

    try:
        local_path, cleanup_download = ensure_local_path(obj)

        # 실제 메뉴판 AI 로직 호출 부분
        result = run_menu_model(local_path)
        return MenuAnalyzeResponse(ok=True, result=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cleanup_download()
        # 추후 로직 완성 후 삭제 처리 진행
        # delete_input_file(file_key=obj.file_key)
