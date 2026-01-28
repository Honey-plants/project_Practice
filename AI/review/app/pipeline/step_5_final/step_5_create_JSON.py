# ai/review/app/pipeline/steps/build_json/run.py
from __future__ import annotations

from AI.review.app.domain.schemas import PipelineContext, FinalReceiptResponse


def run_build_final_response(ctx: PipelineContext) -> PipelineContext:
    ctx.final = FinalReceiptResponse(
        store_name=ctx.store.store_name,
        address=ctx.store.address,
        city=ctx.store.city,
        phone=ctx.extracted.phone,
        coords=ctx.store.coords,
        menu_name=ctx.extracted.menu_ko,
    )
    return ctx
