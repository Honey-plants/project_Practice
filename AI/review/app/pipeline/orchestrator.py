from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

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
# from ai.review.app.pipeline.step_4_enrich_data.step_4_enrich import

# step5 (optional) - final response builder
# from ai.review.app.pipeline.step_5_final.step_5_create_JSON import

@dataclass(frozen=True)
class PipelineConfig:
    # global
    mode: str = "prod"  # "prod" | "debug"

    # step1
    rectify_cfg: RectifyConfig = RectifyConfig()
    rectify_out_dir: Path = Path("debug/step1")

    # step2
    ocr_cfg: Optional[OCRConfig] = None
    ocr_out_dir: Path = Path("debug/step2")

    # step3
    normalize_cfg: NormalizeConfig = NormalizeConfig()
    normalize_out_dir: Path = Path("debug/step3")  # (optional if you want debug artifacts)

    # # step4
    # enrich_cfg: EnrichDataConfig = EnrichDataConfig()
    # enrich_out_dir: Path = Path("debug/step4")  # (optional)
    #
    # # step5
    # build_cfg: BuildJsonConfig = BuildJsonConfig()
    # build_out_dir: Path = Path("debug/step5")  # (optional)

def run_pipeline(
    *,
    input_image_path: str,
    cfg: PipelineConfig,
) -> Dict[str, Any]:
    """
    Orchestrates: step1 -> step2 -> step3 -> step4 -> step5
    Returns final payload (dict) for API response.
    """

    # 0) init ctx
    ctx = PipelineContext(mode=cfg.mode)
    ctx.images.input_path = input_image_path

    # 1) rectify
    ctx = run_step1_rectify(
        ctx,
        out_dir=cfg.rectify_out_dir,
        cfg=cfg.rectify_cfg,
    )

    # 2) OCR
    ctx = run_step2_ocr(
        ctx,
        out_dir=cfg.ocr_out_dir,
        cfg=cfg.ocr_cfg,
    )

    # 3) normalize
    ctx = run_step3_normalize(
        ctx,
        cfg=cfg.normalize_cfg,
    )

    # # 4) enrich (naver store lookup etc.)
    # ctx = run_step4_enrich_data(
    #     ctx,
    #     cfg=cfg.enrich_cfg,
    # )
    #
    # # 5) final json
    # payload = run_step5_build_json(
    #     ctx,
    #     cfg=cfg.build_cfg,
    #     out_dir=cfg.build_out_dir,  # you can ignore if you don't save
    # )

    return