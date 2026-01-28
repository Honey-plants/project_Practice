import base64
import json

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from pathlib import Path

from backend.app.core.security.deps import get_current_member
from backend.app.common.service.file_upload_service import (
    upload_input_file, ensure_local_path, delete_input_file
)
from backend.app.common.schemas.file_upload_schema import UploadInputResponse
from backend.app.core.job_queue import connect_redis, enqueue_task, utc_now_iso

router = APIRouter(prefix="/menu", tags=["menu"])


def _parse_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


@router.post("/upload", response_model=UploadInputResponse)
async def menu_upload(type: str = Form("menu"), image: UploadFile = File(...), current=Depends(get_current_member),):

    obj = await upload_input_file(upload_type=type, member_id=current.member_id, upload=image)

    print("obj :: ", obj)

    cleanup_download = lambda: None

    try:
        # local/s3 ������� �������� '���� ���' ����
        local_path, cleanup_download = ensure_local_path(obj)
        local_path = Path(local_path)

        if not local_path.exists():
            raise FileNotFoundError(f"local_path not found: {local_path}")

        # 버튼 클릭 시 서버가 만든 파일명(stored_file_name)을 run_id로 사용
        # ex) stored_file_name = "menu_20260127_103012_abcd.jpg" -> run_id = "menu_20260127_103012_abcd"
        run_id = Path(obj.stored_file_name).stem

        # orchestrator 실행
        runs_root = Path(_default_runs_root())
        orch = PipelineOrchestrator(runs_root=runs_root)

        run_dir = orch.run(
            image_path=local_path,
            run_id=run_id,
            # orchestrator 기본 옵션 사용 (필요시 여기에 옵션 추가)
        )

        # 산출물 경로 (orchestrator.py 기준)
        rectified_path = run_dir / "rectify" / "rectified.jpg"
        final_json_path = run_dir / "final" / "final.json"

        if not rectified_path.exists():
            raise FileNotFoundError(f"rectified.jpg missing: {rectified_path}")
        if not final_json_path.exists():
            raise FileNotFoundError(f"final.json missing: {final_json_path}")

        return UploadInputResponse(
            upload_type=obj.upload_type,
            member_id=obj.member_id,
            file_key=obj.file_key,
            stored_file_name=obj.stored_file_name,
            org_file_name=obj.org_file_name,
            mime_type=obj.mime_type,
            size_bytes=obj.size_bytes,

            # 응답 확장 필드 (스키마에 Optional로 추가 필요)
            run_id=run_id,
            rectified_path=str(rectified_path),
            final_json_path=str(final_json_path),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        print("마지막 진짜 마지막! finally")
        # s3 다운로드 임시 파일 정리
        cleanup_download()
        # 업로드 입력파일 정리 (local: 파일 삭제 / s3: object 삭제)
        delete_input_file(file_key=obj.file_key)


@router.post("/assistant", status_code=202)
async def enqueue_menu_assistant(
    image: UploadFile = File(...),
    user_profile_json: str = Form(None),
    run_step4: str = Form("true"),
    run_step5: str = Form("true"),
    run_step6: str = Form("true"),
    current=Depends(get_current_member),
):
    try:
        contents = await image.read()
        encoded_image = base64.b64encode(contents).decode("utf-8")

        user_profile = None
        if user_profile_json:
            user_profile = json.loads(user_profile_json)
            if not isinstance(user_profile, dict):
                raise ValueError("user_profile_json must be a JSON object")

        payload = {
            "image_base64": encoded_image,
            "user_profile": user_profile,
            "run_step4": _parse_bool(run_step4, True),
            "run_step5": _parse_bool(run_step5, True),
            "run_step6": _parse_bool(run_step6, True),
            "member_id": getattr(current, "member_id", None),
        }

        r = connect_redis()
        job_id = enqueue_task(r, task="menu_assistant_pipeline", payload=payload)
        return {
            "job_id": job_id,
            "status": "PENDING",
            "queued_at": utc_now_iso(),
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in user_profile_json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
