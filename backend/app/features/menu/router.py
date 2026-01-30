# router.py
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from backend.app.core.security.deps import get_current_member
from backend.app.common.service.file_upload_service import (
    upload_input_file, ensure_local_path
)
from backend.app.common.schemas.file_upload_schema import MenuUploadResponse

from .menu_pipeline_service import run_menu_pipeline, resolve_run_dir

router = APIRouter(prefix="/menu", tags=["menu"])


@router.post("/upload", response_model=MenuUploadResponse)
async def menu_upload(
    type: str = Form("menu"),
    image: UploadFile = File(...),
    current=Depends(get_current_member),
):
    obj = await upload_input_file(upload_type=type, member_id=current.member_id, upload=image)

    cleanup_download = lambda: None

    try:
        local_path, cleanup_download = ensure_local_path(obj)

        # ✅ orchestrator는 오래 걸릴 수 있으니 threadpool에서 실행
        result = await run_in_threadpool(run_menu_pipeline, local_path)

        # ✅ 프론트가 접근 가능한 URL
        rectified_url = f"/menu/runs/{result.run_id}/rectified"
        translate_json_url = f"/menu/runs/{result.run_id}/translate"

        return MenuUploadResponse(
            upload_type=obj.upload_type,
            member_id=obj.member_id,
            file_key=obj.file_key,
            stored_file_name=obj.stored_file_name,
            org_file_name=obj.org_file_name,
            mime_type=obj.mime_type,
            size_bytes=obj.size_bytes,

            run_id=result.run_id,
            run_dir=str(result.run_dir),
            rectified_path=str(result.rectified_path),
            translate_json_path=str(result.translate_json_path),

            rectified_url=rectified_url,
            translate_json_url=translate_json_url,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 정책에 따라 켜기
        # cleanup_download()
        pass


# ============================================================
# ✅ 프론트가 실제로 파일을 가져갈 수 있는 서빙 라우트
# ============================================================

@router.get("/runs/{run_id}/rectified")
async def get_rectified(run_id: str):
    try:
        run_dir = resolve_run_dir(run_id)
        path = run_dir / "rectify" / "rectified.jpg"
        if not path.exists():
            raise HTTPException(status_code=404, detail="rectified.jpg not found")

        return FileResponse(
            path=str(path),
            media_type="image/jpeg",
            filename="rectified.jpg",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs/{run_id}/translate")
async def get_translate_json(run_id: str):
    try:
        run_dir = resolve_run_dir(run_id)
        path = run_dir / "translate" / "translate.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="translate.json not found")

        return FileResponse(
            path=str(path),
            media_type="application/json",
            filename="translate.json",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
