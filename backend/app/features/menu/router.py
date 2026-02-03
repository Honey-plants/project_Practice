import uuid
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.core.security.deps import get_current_member
from backend.app.common.utils.debug import log_exception
from backend.app.common.service.file_upload_service import (
    build_temp_prefix,
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
    user_profile: str = Form(""),  # JSON 문자열
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
        # runs_root 생성
        runs_root = Path(tmp_prefix) / "ai_runs"
        runs_root.mkdir(parents=True, exist_ok=True)

        # ✅ run_dir를 먼저 확정
        run_dir = runs_root / job_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # ✅ user_profile 저장 (run_dir 내부)
        user_profile_json_path = None
        profile_raw = (user_profile or "").strip()

        # 디버그(필요 시 유지): 실제로 들어오는지 확인
        # print("[DEBUG] user_profile len =", len(profile_raw))

        if profile_raw:
            try:
                profile_obj = json.loads(profile_raw)
                if not isinstance(profile_obj, dict):
                    raise ValueError("user_profile must be a JSON object")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"user_profile invalid JSON: {e}")

            profile_dir = run_dir / "profile"
            profile_dir.mkdir(parents=True, exist_ok=True)
            user_profile_json_path = profile_dir / "user_profile.json"
            user_profile_json_path.write_text(
                json.dumps(profile_obj, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # orchestrator 실행
        result = run_menu_ai(
            image_path=local_path,
            runs_root=runs_root,
            run_id=job_id,
            user_profile_json=str(user_profile_json_path) if user_profile_json_path else None,
        )

        return MenuUploadResponse(job_id=job_id, upload_type="menu", result=result)

    except HTTPException:
        raise
    except Exception as e:
        log_exception("menu.ai_failed", e)
        raise HTTPException(status_code=500, detail=f"menu ai failed: {type(e).__name__}: {e}")
    finally:
        cleanup()
