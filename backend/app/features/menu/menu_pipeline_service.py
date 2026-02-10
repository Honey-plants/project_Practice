# menu_pipeline_service.py
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from AI.menu_assistant.worker.worker_app.pipeline.orchestrator import (
    PipelineOrchestrator,
    _default_runs_root,
)

_RUN_ID_RE = re.compile(r"^\d{8}_\d{6}$")  # 20260130_153012 형태

@dataclass(frozen=True)
class MenuPipelineResult:
    run_id: str
    run_dir: Path
    rectified_path: Path
    translate_json_path: Path


def run_menu_pipeline(local_path: str) -> MenuPipelineResult:
    img_path = Path(local_path)
    if not img_path.exists():
        raise FileNotFoundError(f"Input image not found: {img_path}")

    orch = PipelineOrchestrator(runs_root=_default_runs_root())
    run_dir: Path = orch.run(img_path)

    rectified = run_dir / "rectify" / "rectified.jpg"
    translate_json = run_dir / "translate" / "translate.json"

    if not rectified.exists():
        raise FileNotFoundError(f"rectified.jpg not found: {rectified}")
    if not translate_json.exists():
        raise FileNotFoundError(f"translate.json not found: {translate_json}")

    return MenuPipelineResult(
        run_id=run_dir.name,
        run_dir=run_dir,
        rectified_path=rectified,
        translate_json_path=translate_json,
    )


def resolve_run_dir(run_id: str) -> Path:
    """
    run_id로 runs/<run_id> 디렉토리를 안전하게 찾는다 (path traversal 방지).
    """
    if not _RUN_ID_RE.match(run_id):
        raise ValueError("Invalid run_id format")

    runs_root = _default_runs_root()
    run_dir = (runs_root / run_id).resolve()

    # runs_root 밖으로 탈출하는 케이스 방지
    runs_root_resolved = runs_root.resolve()
    if runs_root_resolved not in run_dir.parents:
        raise ValueError("Invalid run_id path")

    return run_dir
