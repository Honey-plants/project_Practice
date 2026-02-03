import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.core import config
from backend.app.core.security.deps import get_current_member
from backend.app.common.utils.debug import log_exception
from backend.app.common.service.file_upload_service import (
    build_temp_prefix,
    delete_prefix,
    ensure_local_path,
    upload_input_file,
)
from backend.app.features.menu.schemas import MenuUploadResponse

from backend.app.features.menu.service import run_menu_ai

router = APIRouter(prefix="/menu", tags=["menu"])


@router.post("/upload", response_model=MenuUploadResponse)
async def upload_menu(
    type: str = Form("menu"),
    file: UploadFile = File(...),
    current=Depends(get_current_member),
):
    if (type or "").lower().strip() != "menu":
        raise HTTPException(status_code=400, detail="type must be 'menu'")

    job_id = uuid.uuid4().hex
    tmp_prefix = build_temp_prefix(upload_type="menu", scope_id=job_id)

    try:
        obj = await upload_input_file(
            upload_type="menu",
            member_id=current.member_id,
            upload=file,
            scope_id=job_id,
            is_temp=True,
        )
    except Exception as e:
        log_exception("menu.upload_input", e)
        raise HTTPException(status_code=400, detail=f"upload failed: {e}")

    local_path, cleanup = ensure_local_path(obj)

    try:
        #  runs_root는 temp 아래로 두어도 됨(디버그 목적)
        runs_root = Path(tmp_prefix) / "ai_runs"

        result = run_menu_ai(image_path=local_path, runs_root=runs_root, run_id=job_id)
        return MenuUploadResponse(job_id=job_id, upload_type="menu", result=result)

    except Exception as e:
        log_exception("menu.ai_failed", e)
        raise HTTPException(status_code=500, detail=f"menu ai failed: {type(e).__name__}: {e}")

    finally:
        cleanup()
        #  menu 정책: 작업 끝나면 temp 삭제
        # delete_prefix(prefix_key=tmp_prefix)
