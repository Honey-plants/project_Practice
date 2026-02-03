# menu_assistant/worker/worker_app/pipeline/steps/config.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# -------------------------
# IDs / defaults
# -------------------------

def default_run_id() -> str:
    """Timestamp-based run id (stable, human readable)."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def repo_root_from_steps_file(steps_file: str) -> Path:
    """
    steps/*.py 기준으로 repository root(menu_assistant/)를 유추한다.
    steps_file = __file__ 을 넘겨서 사용.
    """
    # .../menu_assistant/worker/worker_app/pipeline/steps/config.py
    return Path(steps_file).resolve().parents[4]  # menu_assistant/


def default_data_dir_from_steps_file(steps_file: str) -> Path:
    """Default data_dir = <repo_root>/data"""
    return repo_root_from_steps_file(steps_file) / "data"


# -------------------------
# Run directory resolving
# -------------------------

@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    input_dir: Path
    rectify_dir: Path
    ocr_dir: Path
    normalize_dir: Path
    rag_match_dir: Path
    llm_dir: Path
    translate_dir: Path
    final_dir: Path


def resolve_run_dir(*, data_dir: Path, run_id: str, run_dir: Optional[Path] = None) -> Path:
    """
    공통 run_dir 규약:
      - run_dir가 주어지면 그것을 사용
      - 아니면 <data_dir>/runs/<run_id>
    """
    return run_dir if run_dir is not None else (data_dir / "runs" / run_id)


def build_run_paths(*, data_dir: Path, run_id: str, run_dir: Optional[Path] = None) -> RunPaths:
    rd = resolve_run_dir(data_dir=data_dir, run_id=run_id, run_dir=run_dir)
    return RunPaths(
        run_dir=rd,
        input_dir=rd / "input",
        rectify_dir=rd / "rectify",
        ocr_dir=rd / "ocr",
        normalize_dir=rd / "normalize",
        rag_match_dir=rd / "rag_match",
        llm_dir=rd / "llm",
        translate_dir=rd / "translate",
        final_dir=rd / "final",
    )


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


# -------------------------
# JSON helpers
# -------------------------

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any, *, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


# -------------------------
# CLI compatibility helpers
# -------------------------

def coalesce_str(*values: Any) -> Optional[str]:
    """Return the first non-empty string value."""
    for v in values:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def coalesce_path(*values: Any) -> Optional[Path]:
    """Return the first existing/meaningful path among args."""
    for v in values:
        if v is None:
            continue
        p = Path(v)
        # 존재 여부로 강제하면 아직 생성 전 경로가 있을 수 있어 None 처리될 수 있음
        # -> 여기서는 문자열이 유효하면 그대로 반환
        return p
    return None
