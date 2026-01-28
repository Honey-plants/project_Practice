from __future__ import annotations

from pathlib import Path
from typing import Optional

from AI.review.app.domain.schemas import PipelineContext, OCRItem
from AI.review.app.pipeline.step_2_ocr.ocr_model import OCRConfig
from AI.review.app.pipeline.step_2_ocr.run_ocr import run_receipt_ocr  # 네가 만든 step2 엔트리 (payload["items"] 반환)


def run_step2_ocr(ctx: PipelineContext, *, out_dir: Path, cfg: Optional[OCRConfig] = None) -> PipelineContext:
    out_dir.mkdir(parents=True, exist_ok=True)

    # step1 결과가 있으면 rectified_path 쓰고, 없으면 input_path라도 허용
    img_path = ctx.images.rectified_path or ctx.images.input_path
    if not img_path:
        raise ValueError("Need ctx.images.rectified_path or ctx.images.input_path")

    payload = run_receipt_ocr(
        image_path=Path(img_path),
        out_dir=out_dir,
        cfg=cfg,
        save_overlay=True,
        save_json=(ctx.mode == "debug"),
    )

    # ✅ items를 OCRItem으로 검증/변환
    ctx.ocr.items = [OCRItem(**it) for it in payload["items"]]
    ctx.ocr.n_items = payload["n_items"]
    ctx.ocr.overlay_path = payload["outputs"].get("overlay")

    if ctx.mode == "debug":
        if "json" in payload["outputs"]:
            ctx.debug.jsons["ocr_result"] = payload["outputs"]["json"]
        if "overlay" in payload["outputs"]:
            ctx.debug.images["ocr_overlay"] = payload["outputs"]["overlay"]

    return ctx
