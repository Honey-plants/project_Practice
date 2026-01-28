# ai/review/app/pipeline/step_1_rectify/run.py
from __future__ import annotations

from pathlib import Path
from AI.review.app.domain.schemas import PipelineContext
from AI.review.app.pipeline.step_1_rectify.run_rectify import RectifyConfig, run_receipt_rectify


def run_step1_rectify(ctx: PipelineContext, *, out_dir: Path, cfg: RectifyConfig) -> PipelineContext:
    out_dir.mkdir(parents=True, exist_ok=True)

    # 입력 경로는 ctx.images.input_path에 있다고 가정
    if not ctx.images.input_path:
        raise ValueError("ctx.images.input_path is required")

    res = run_receipt_rectify(
        image_path=Path(ctx.images.input_path),
        out_dir=out_dir,
        cfg=cfg,
    )

    # ✅ step1 contract: rectified 결과 경로 저장
    # 네가 저장하던 파일명 기준으로 매핑
    rectified_path = out_dir / "20_post_for_ocr.jpg"
    cropped_path = out_dir / "12_cropped.jpg"

    ctx.images.cropped_path = str(cropped_path)
    ctx.images.rectified_path = str(rectified_path)

    if ctx.mode == "debug":
        ctx.debug.images.update({
            "00_original": str(out_dir / "00_original.jpg"),
            "01_pre_for_crop": str(out_dir / "01_pre_for_crop.jpg"),
            "10_edges": str(out_dir / "10_edges.jpg"),
            "11_quad_overlay": str(out_dir / "11_quad_overlay.jpg"),
            "12_cropped": str(cropped_path),
            "20_post_for_ocr": str(rectified_path),
        })

    return ctx
