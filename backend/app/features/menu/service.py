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

    # runs_root는 router에서 넘겨준 tmp 경로를 그대로 사용
    # 예: C:\...\uploads\tmp\menu\<job_id>\ai_runs
    runs_root = Path(runs_root).resolve()
    runs_root.mkdir(parents=True, exist_ok=True)

    orch = PipelineOrchestrator(runs_root, data_dir=menu_data_dir)

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

    # 이하 final json + rectified base64 반환 로직은 그대로

    # ---- step6 output: final_translated.json ----
    result_path = run_dir / "final" / "final_translated.json"

    if not result_path.exists():
        # step6가 비활성/실패했을 때만 fallback
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
    }
