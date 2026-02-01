import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.common.service.file_upload_service import (
    build_temp_prefix,
    delete_prefix,
    ensure_local_path,
    upload_input_file,
)
from backend.app.core.security.deps import get_current_member
from backend.app.features.menu.schemas import MenuResultResponse, MenuUploadResponse
from backend.app.features.menu.service import MenuJobStore, run_menu_ai

router = APIRouter(prefix="/menu", tags=["menu"])


@router.post("/upload", response_model=MenuUploadResponse)
async def upload_menu(
    type: str = Form("menu"),
    file: UploadFile = File(...),
    current=Depends(get_current_member),
):
    print("menu 진입")

    if (type or "").lower() not in ("menu",):
        raise HTTPException(status_code=400, detail="type must be 'menu'")

    job_id = uuid.uuid4().hex

    try:
        obj = await upload_input_file(
            upload_type="menu",
            member_id=current.member_id,
            upload=file,
            scope_id=job_id,
            is_temp=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    local_path, cleanup = ensure_local_path(obj)
    tmp_prefix = build_temp_prefix(upload_type="menu", scope_id=job_id)

    try:
        runs_root = Path(tmp_prefix) / "ai_runs"
        result = run_menu_ai(image_path=local_path, runs_root=runs_root, run_id=job_id)

        MenuJobStore.put(job_id=job_id, member_id=current.member_id, result=result)

        # (디버그) result.json 한번 생성 후 바로 삭제(폴더 삭제로 같이 정리)
        try:
            p = Path(tmp_prefix) / "result.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        return MenuUploadResponse(job_id=job_id, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"menu ai failed: {type(e).__name__}: {e}")
    finally:
        cleanup()
        delete_prefix(prefix_key=tmp_prefix)


@router.get("/result/{job_id}", response_model=MenuResultResponse)
def get_menu_result(job_id: str, current=Depends(get_current_member)):
    data = MenuJobStore.get(job_id=job_id)
    if not data:
        raise HTTPException(status_code=404, detail="menu result expired")
    if int(data.get("member_id") or 0) != int(current.member_id):
        raise HTTPException(status_code=403, detail="forbidden")
    return MenuResultResponse(job_id=job_id, result=data.get("result") or {})
