from __future__ import annotations
from dataclasses import dataclass

from AI.review.app.domain.schemas import PipelineContext
from AI.review.app.pipeline.step_3_normalize.run_normalize import normalize_receipt_data

@dataclass(frozen=True)
class NormalizeConfig:
    y_threshold: int = 15

def run_step3_normalize(ctx: PipelineContext, *, cfg: NormalizeConfig) -> PipelineContext:
    if not ctx.ocr.items:
        raise ValueError("ctx.ocr.items is empty. Run step2 first.")

    normalized = normalize_receipt_data(
        [it.model_dump() for it in ctx.ocr.items],
        y_threshold=cfg.y_threshold,
    )

    ctx.normalize.lines = normalized["lines"]
    ctx.extracted.phone = normalized["phone"]
    ctx.extracted.menu_ko = normalized["menu_ko"]

    return ctx





