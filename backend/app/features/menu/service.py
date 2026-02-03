from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.core import config


def run_menu_ai(
    *,
    image_path: str,
    runs_root: Path,
    run_id: str,
    user_profile_json: Optional[str] = None,
) -> Dict[str, Any]:
    from AI.menu_assistant.worker.worker_app.pipeline.orchestrator import (
        PipelineOrchestrator,
        Step5Options,
    )

    menu_data_dir = (config.PROJECT_ROOT / "AI" / "menu_assistant" / "data").resolve()

    runs_root = Path(runs_root).resolve()
    runs_root.mkdir(parents=True, exist_ok=True)

    # ✅ 프로필 fallback 명시용 메타
    if user_profile_json:
        profile_source = "provided"
        profile_used = None  # 제공된 파일 내용까지 굳이 응답에 싣지 않음(필요하면 읽어서 넣을 수 있음)
    else:
        profile_source = "default"
        profile_used = {"allergy_tags": [], "avoid_foods": [], "religion": None}

    orch = PipelineOrchestrator(runs_root, data_dir=menu_data_dir)

    # Step05는 user_profile_json이 None/""이면 내부에서 안전 기본값 사용함
    step5 = Step5Options(user_profile_json=user_profile_json)

    run_dir = orch.run(
        image_path=Path(image_path).resolve(),
        run_id=run_id,
        step5=step5,
        run_step4=True,
        run_step5=True,
        run_step6=True,
        do_check=False,
    )

    # ---- step6 output: final_translated.json ----
    result_path = run_dir / "final" / "final_translated.json"
    if not result_path.exists():
        fallback_path = run_dir / "final" / "final.json"
        if fallback_path.exists():
            result_path = fallback_path
        else:
            raise FileNotFoundError(
                f"Menu result not found: {result_path} (and fallback missing: {fallback_path})"
            )

    final_obj = json.loads(result_path.read_text(encoding="utf-8"))

    # ---- rectified image (base64) ----
    rectified_path = run_dir / "rectify" / "rectified.jpg"
    if not rectified_path.exists():
        raise FileNotFoundError(f"Rectified image not found: {rectified_path}")

    img_b64 = base64.b64encode(rectified_path.read_bytes()).decode("ascii")

    return {
        "final": final_obj,
        "rectified_image": {
            "mime": "image/jpeg",
            "base64": img_b64,
        },
        "run_id": run_id,
        # ✅ 프론트/디버그용: 이번 분석에 어떤 프로필이 적용됐는지 명시
        "meta": {
            "profile_source": profile_source,  # "provided" | "default"
            "profile_used": profile_used,      # default일 때만 채움
        },
    }
