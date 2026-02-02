import json
from pathlib import Path
from typing import Any, Dict

from backend.app.core import config


def run_menu_ai(*, image_path: str, runs_root: Path, run_id: str) -> Dict[str, Any]:
    from AI.menu_assistant.worker.worker_app.pipeline.orchestrator import PipelineOrchestrator, Step5Options

    #  menu assistant 데이터 디렉토리는 반드시 여기
    menu_data_dir = (config.PROJECT_ROOT / "AI" / "menu_assistant" / "data").resolve()

    orch = PipelineOrchestrator(Path(runs_root), data_dir=menu_data_dir)

    step5 = Step5Options(user_profile_json=None)

    run_dir = orch.run(
        image_path=Path(image_path).resolve(),
        run_id=run_id,
        step5=step5,
        run_step4=True,
        run_step5=True,
        run_step6=True,
        do_check=False,
    )

    result_path = run_dir / "final" / "final_translated.json"
    if not result_path.exists():
        result_path = run_dir / "final" / "final.json"
    if not result_path.exists():
        raise FileNotFoundError(f"Menu result not found: {result_path}")

    return json.loads(result_path.read_text(encoding="utf-8"))
