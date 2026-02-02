from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json
import uuid
from copy import deepcopy

from AI.review.app.domain.schemas import PipelineContext

# step0
from AI.review.app.pipeline.step_1_rectify.step0_preprocess import (
    run_step0_preprocess,
    Step0PreprocessConfig,
)

# step1
from AI.review.app.pipeline.step_1_rectify.step_1_rectify import run_step1_rectify
from AI.review.app.pipeline.step_1_rectify.run_rectify import RectifyConfig

# step2
from AI.review.app.pipeline.step_2_ocr.step_2_ocr import run_step2_ocr
from AI.review.app.pipeline.step_2_ocr.ocr_model import OCRConfig
from AI.review.app.pipeline.step_2_ocr.access_ocr_quality import assess_ocr_quality, is_bad_quality

# step3
from AI.review.app.pipeline.step_3_normalize.step_3_normalize import run_step3_normalize, NormalizeConfig

# step4
from AI.review.app.pipeline.step_4_enrich_data.step_4_enrich import run_step4_enrich

# step5
from AI.review.app.pipeline.step_5_final.step_5_create_JSON import run_build_final_response


def make_run_dir(base: Path, name: str | None = None) -> Path:
    ts = datetime.now().strftime("%Y%m%d%H%M")
    folder = ts if not name else f"{ts}_{name}"
    run_dir = base / folder
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _items_to_dicts(items) -> list[dict]:
    out = []
    for it in items or []:
        if isinstance(it, dict):
            out.append(it)
        elif hasattr(it, "model_dump"):
            out.append(it.model_dump())
        elif hasattr(it, "dict"):
            out.append(it.dict())
        else:
            out.append({"score": 0.0})
    return out


@dataclass(frozen=True)
class PipelineConfig:
    mode: str = "prod"
    test_base_dir: Path = Path("AI/review/test")
    run_name: Optional[str] = None

    # step0 (기본 전처리)
    step0_cfg: Step0PreprocessConfig = Step0PreprocessConfig()

    # step1
    rectify_cfg: RectifyConfig = RectifyConfig()

    # step2
    ocr_cfg: Optional[OCRConfig] = None

    # step3
    normalize_cfg: NormalizeConfig = NormalizeConfig()

    # step4
    naver_cfg: Optional[Dict[str, str]] = None
    gemini_api_key: Optional[str] = None

    # OCR gate
    ocr_low_cut: float = 0.6


def run_pipeline(*, input_image_path: str, cfg: PipelineConfig) -> Dict[str, Any]:
    run_dir = make_run_dir(base=cfg.test_base_dir, name=cfg.run_name)

    step0_dir = run_dir / "step0_preprocess"
    step1_dir = run_dir / "step1_rectify"
    step2_dir = run_dir / "step2_ocr"
    step3_dir = run_dir / "step3_normalize"
    step4_dir = run_dir / "step4_enrich"
    step5_dir = run_dir / "step5_final"

    ctx = PipelineContext(mode=cfg.mode)
    ctx.job_id = str(uuid.uuid4())
    ctx.images.input_path = input_image_path

    # =========================
    # Step0: 가벼운 OCR-friendly preprocess
    # =========================
    step0 = run_step0_preprocess(
        input_image_path=ctx.images.input_path,
        out_dir=step0_dir,
        cfg=cfg.step0_cfg,
    )
    pre_ocr_path = step0["pre_ocr_path"]

    if cfg.mode == "debug":
        ctx.debug.jsons["step0_meta"] = str(step0_dir / "meta.json")
        ctx.debug.images["step0_pre_ocr"] = pre_ocr_path

    # =========================
    # 1) OCR 1차: step0 결과로 OCR
    # =========================
    ctx_ocr1 = run_step2_ocr(
        ctx,
        out_dir=step2_dir / "pass1_pre",
        cfg=cfg.ocr_cfg,
        image_path=pre_ocr_path,
    )

    q1 = assess_ocr_quality(_items_to_dicts(ctx_ocr1.ocr.items), low_cut=cfg.ocr_low_cut)
    bad1 = is_bad_quality(q1)

    (step2_dir / "pass1_pre").mkdir(parents=True, exist_ok=True)
    (step2_dir / "pass1_pre" / "quality.json").write_text(json.dumps(q1, ensure_ascii=False, indent=2), encoding="utf-8")

    # =========================
    # 2) 품질 나쁘면: rectify(원본) + OCR 2차
    # =========================
    if bad1:
        ctx2 = deepcopy(ctx)

        # rectify는 step0 이미지 말고 "원본" 기반이 더 안정적
        ctx2.images.input_path = input_image_path
        ctx2 = run_step1_rectify(ctx2, out_dir=step1_dir, cfg=cfg.rectify_cfg)

        ocr_src2 = ctx2.images.rectified_path or ctx2.images.cropped_path or ctx2.images.input_path

        ctx_ocr2 = run_step2_ocr(
            ctx2,
            out_dir=step2_dir / "pass2_rectified",
            cfg=cfg.ocr_cfg,
            image_path=ocr_src2,
        )

        q2 = assess_ocr_quality(_items_to_dicts(ctx_ocr2.ocr.items), low_cut=cfg.ocr_low_cut)

        (step2_dir / "pass2_rectified").mkdir(parents=True, exist_ok=True)
        (step2_dir / "pass2_rectified" / "quality.json").write_text(json.dumps(q2, ensure_ascii=False, indent=2), encoding="utf-8")

        def better(a: dict, b: dict) -> bool:
            # avg 우선, p10도 고려, 같으면 low_ratio 작은 게 승
            if a["avg"] != b["avg"]:
                return a["avg"] > b["avg"]
            if a["p10"] != b["p10"]:
                return a["p10"] > b["p10"]
            return a["low_ratio"] < b["low_ratio"]

        ctx = ctx_ocr2 if better(q2, q1) else ctx_ocr1
    else:
        ctx = ctx_ocr1

    # =========================
    # step3 이후 동일
    # =========================
    ctx = run_step3_normalize(ctx, cfg=cfg.normalize_cfg)

    step3_dir.mkdir(parents=True, exist_ok=True)
    (step3_dir / "step3_result.json").write_text(
        json.dumps(ctx.model_dump() if hasattr(ctx, "model_dump") else ctx.dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not cfg.gemini_api_key:
        raise ValueError("Missing gemini_api_key ...")

    naver_cfg = cfg.naver_cfg or {}
    ctx = run_step4_enrich(ctx, naver_cfg=naver_cfg, gemini_api_key=cfg.gemini_api_key)

    step4_dir.mkdir(parents=True, exist_ok=True)
    (step4_dir / "ctx_after_step4.json").write_text(
        json.dumps(ctx.model_dump() if hasattr(ctx, "model_dump") else ctx.dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ctx = run_build_final_response(ctx)
    final_payload = ctx.final.model_dump() if hasattr(ctx.final, "model_dump") else ctx.final.dict()

    step5_dir.mkdir(parents=True, exist_ok=True)
    (step5_dir / "final.json").write_text(
        json.dumps(final_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"run_dir": str(run_dir), "final": final_payload}


# from __future__ import annotations
#
# import json
# import uuid
# from dataclasses import dataclass
# from datetime import datetime
# from pathlib import Path
# from typing import Any, Dict, Optional
#
# # ---- Domain ----
# from AI.review.app.domain.schemas import PipelineContext
#
# # ---- Step 1 ----
# from AI.review.app.pipeline.step_1_rectify.step_1_rectify import run_step1_rectify
# from AI.review.app.pipeline.step_1_rectify.run_rectify import RectifyConfig
#
# # ---- Step 2 ----
# from AI.review.app.pipeline.step_2_ocr.step_2_ocr import run_step2_ocr
# from AI.review.app.pipeline.step_2_ocr.ocr_model import OCRConfig
#
# # ---- Step 3 ----
# from AI.review.app.pipeline.step_3_normalize.step_3_normalize import run_step3_normalize, NormalizeConfig
#
# # ---- Step 4 ----
# from AI.review.app.pipeline.step_4_enrich_data.step_4_enrich import run_step4_enrich
#
# # ---- Step 5 ----
# from AI.review.app.pipeline.step_5_final.step_5_create_JSON import run_build_final_response
#
#
# def make_run_dir(base: Path, name: str | None = None) -> Path:
#     """
#     run 결과 디렉터리 생성
#     예: <base>/<YYYYMMDDHHMM>_<name>/
#     """
#     base = Path(base)
#     base.mkdir(parents=True, exist_ok=True)
#
#     ts = datetime.now().strftime("%Y%m%d%H%M")
#     folder = ts if not name else f"{ts}_{name}"
#     run_dir = base / folder
#     run_dir.mkdir(parents=True, exist_ok=False)
#     return run_dir
#
#
# @dataclass(frozen=True)
# class PipelineConfig:
#     """
#     - test_base_dir: run 결과 저장 루트
#       (너 정책: uploads/tmp/receipt/<id>/runs 에 넣고 싶으면 backend에서 이 값을 그 경로로 넘겨주면 됨)
#     """
#     mode: str = "prod"
#     test_base_dir: Path = Path("AI/review/test")
#     run_name: Optional[str] = None
#
#     rectify_cfg: RectifyConfig = RectifyConfig()
#     ocr_cfg: Optional[OCRConfig] = None
#     normalize_cfg: NormalizeConfig = NormalizeConfig()
#
#     # step4에서 사용
#     naver_cfg: Optional[Dict[str, str]] = None
#     gemini_api_key: Optional[str] = None
#
#
# def _dump_json(path: Path, data: Any) -> None:
#     path.parent.mkdir(parents=True, exist_ok=True)
#     try:
#         if hasattr(data, "model_dump"):
#             data = data.model_dump()
#         elif hasattr(data, "dict"):
#             data = data.dict()
#         path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
#     except Exception:
#         # 실패해도 파이프라인은 진행
#         pass
#
#
# def run_pipeline(*, input_image_path: str, cfg: PipelineConfig) -> Dict[str, Any]:
#     """
#      Receipt FULL Pipeline (Step1~Step5)
#     - Step1: rectify
#     - Step2: OCR
#     - Step3: normalize
#     - Step4: enrich (naver + gemini)
#     - Step5: final JSON build
#     """
#
#     # 0) run_dir 생성
#     run_dir = make_run_dir(base=cfg.test_base_dir, name=cfg.run_name)
#
#     step1_dir = run_dir / "step1_rectify"
#     step2_dir = run_dir / "step2_ocr"
#     step3_dir = run_dir / "step3_normalize"
#     step4_dir = run_dir / "step4_enrich"
#     step5_dir = run_dir / "step5_final"
#
#     # 1) Context 생성
#     ctx = PipelineContext(mode=cfg.mode)
#     ctx.job_id = str(uuid.uuid4())
#     ctx.images.input_path = str(input_image_path)
#
#     # 2) Step1
#     ctx = run_step1_rectify(ctx, out_dir=step1_dir, cfg=cfg.rectify_cfg)
#     _dump_json(step1_dir / "ctx_after_step1.json", ctx)
#
#     # 3) Step2 (OCR)
#     ctx = run_step2_ocr(ctx, out_dir=step2_dir, cfg=cfg.ocr_cfg)
#     _dump_json(step2_dir / "ctx_after_step2.json", ctx)
#
#     # 4) Step3 (Normalize)
#     ctx = run_step3_normalize(ctx, cfg=cfg.normalize_cfg)
#     _dump_json(step3_dir / "ctx_after_step3.json", ctx)
#
#     # 5) Step4 (Enrich)
#     if not cfg.gemini_api_key:
#         # 정책상 step5까지 돌린다고 했으니, 여기서 키가 없으면 500 원인이 됨
#         raise ValueError("Missing gemini_api_key (required for step4 enrich)")
#
#     naver_cfg = cfg.naver_cfg or {}
#     ctx = run_step4_enrich(ctx, naver_cfg=naver_cfg, gemini_api_key=cfg.gemini_api_key)
#     _dump_json(step4_dir / "ctx_after_step4.json", ctx)
#
#     # 6) Step5 (Final JSON build)
#     ctx = run_build_final_response(ctx)
#
#     # final payload 저장
#     final_payload = None
#     if getattr(ctx, "final", None) is not None:
#         final_payload = ctx.final.model_dump() if hasattr(ctx.final, "model_dump") else ctx.final.dict()
#
#     _dump_json(step5_dir / "final.json", final_payload or {})
#
#     return {
#         "run_dir": str(run_dir),
#         "final": final_payload or {},
#     }

