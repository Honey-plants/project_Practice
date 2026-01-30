from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json
import uuid
from AI.review.app.domain.schemas import PipelineContext

# step1
from AI.review.app.pipeline.step_1_rectify.step_1_rectify import run_step1_rectify
from AI.review.app.pipeline.step_1_rectify.run_rectify import RectifyConfig as RectifyConfig

# step2
from AI.review.app.pipeline.step_2_ocr.step_2_ocr import run_step2_ocr
from AI.review.app.pipeline.step_2_ocr.ocr_model import OCRConfig

# step3
from AI.review.app.pipeline.step_3_normalize.step_3_normalize import run_step3_normalize, NormalizeConfig

# step4
from AI.review.app.pipeline.step_4_enrich_data.step_4_enrich import run_step4_enrich

# step5 (optional) - final response builder
from AI.review.app.pipeline.step_5_final.step_5_create_JSON import run_build_final_response


def make_run_dir(base: Path, name: str | None = None) -> Path:
    ts = datetime.now().strftime("%Y%m%d%H%M")
    folder = ts if not name else f"{ts}_{name}"
    run_dir = base / folder
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir

@dataclass(frozen=True)
class PipelineConfig:
    # global
    mode: str = "prod"  # "prod" | "debug"

    # base folder for one run
    test_base_dir: Path = Path("AI/review/test")
    run_name: Optional[str] = None

    # step1
    rectify_cfg: RectifyConfig = RectifyConfig()

    # step2
    ocr_cfg: Optional[OCRConfig] = None

    # step3
    normalize_cfg: NormalizeConfig = NormalizeConfig()

    naver_cfg: Optional[Dict[str, str]] = None
    gemini_api_key: Optional[str] = None

def run_pipeline(*, input_image_path: str, cfg: PipelineConfig) -> Dict[str, Any]:
    # 0) create per-run folder
    run_dir = make_run_dir(base=cfg.test_base_dir, name=cfg.run_name)

    # step output dirs (✅ timestamp 폴더 안으로)
    step1_dir = run_dir / "step1_rectify"
    step2_dir = run_dir / "step2_ocr"
    step3_dir = run_dir / "step3_normalize"
    step4_dir = run_dir / "step4_enrich"
    step5_dir = run_dir / "step5_final"

    # 0) init ctx
    ctx = PipelineContext(mode=cfg.mode)
    ctx.job_id = str(uuid.uuid4())                  #job_id 로 결과값 저장할 폴더 지정
    ctx.images.input_path = input_image_path

    # 1) rectify
    ctx = run_step1_rectify(ctx, out_dir=step1_dir, cfg=cfg.rectify_cfg)

    # 2) OCR
    ctx = run_step2_ocr(ctx, out_dir=step2_dir, cfg=cfg.ocr_cfg)

    # 3) normalize (너 step3가 out_dir 받는 구조면 넣고, 아니면 ctx.debug.jsons에 저장하도록)
    ctx = run_step3_normalize(ctx, cfg=cfg.normalize_cfg)
    # ✅ step3 결과를 파일로도 남기고 싶으면 (추천)
    (step3_dir).mkdir(parents=True, exist_ok=True)
    (step3_dir / "step3_result.json").write_text(
        json.dumps(ctx.model_dump() if hasattr(ctx, "model_dump") else ctx.dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # step4
    if not cfg.gemini_api_key:
        raise ValueError("Missing gemini_api_key ...")

    naver_cfg = cfg.naver_cfg or {}
    ctx = run_step4_enrich(ctx, naver_cfg=naver_cfg, gemini_api_key=cfg.gemini_api_key)

    # ✅ 추가 (폴더 없으면 만들기)
    # 폴더 생성 추가 위치
    step4_dir.mkdir(parents=True, exist_ok=True)

    (step4_dir / "ctx_after_step4.json").write_text(
        json.dumps(ctx.model_dump() if hasattr(ctx, "model_dump") else ctx.dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 5) final json builder
    ctx = run_build_final_response(ctx)

    final_payload = ctx.final.model_dump() if hasattr(ctx.final, "model_dump") else ctx.final.dict()
    (step5_dir).mkdir(parents=True, exist_ok=True)

    # json 생성 위치
    (step5_dir / "final.json").write_text(
        json.dumps(final_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # 최종 payload 리턴
    return {
        "run_dir": str(run_dir),
        "final": ctx.final.model_dump() if getattr(ctx, "final", None) and hasattr(ctx.final, "model_dump") else None,
    }

