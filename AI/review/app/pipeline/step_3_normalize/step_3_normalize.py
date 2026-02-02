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








# from __future__ import annotations
# from dataclasses import dataclass, asdict
# from typing import Any, Dict, List, Optional
#
# from ai.review.app.domain.schemas import PipelineContext, StoreInfo, Coords
# from ai.review.app.adapters.external.naver_local import find_location
# from ai.review.app.pipeline.step_3_normalize.run_normalize import build_receipt_json
#
# @dataclass(frozen=True)
# class NormalizeConfig:
#     enable_store_lookup: bool = True
#     y_threshold: int = 15
#     naver_client_id: Optional[str] = None
#     naver_client_secret: Optional[str] = None
#
# def run_step3_normalize(ctx: PipelineContext, *, cfg: NormalizeConfig) -> PipelineContext:
#     if not ctx.ocr.items:
#         raise ValueError("ctx.ocr.items is empty. Run step2 first.")
#
#     ctx.normalize.y_threshold = cfg.y_threshold
#
#     # items -> receipt_json (phone/menu + debug_lines)
#     receipt = build_receipt_json(
#         [it.model_dump() for it in ctx.ocr.items],
#         store_info=None,
#         y_threshold=cfg.y_threshold,
#     )
#
#     ctx.normalize.lines = receipt.get("debug_lines", [])
#     ctx.extracted.phone = receipt.get("phone")
#     ctx.extracted.menu_ko = receipt.get("menu_name", [])  # 너 key가 menu_name이면 맞추고, menu_ko면 변경
#
#     # store lookup
#     if cfg.enable_store_lookup and ctx.extracted.phone and cfg.naver_client_id and cfg.naver_client_secret:
#         store_info = find_location(
#             ctx.extracted.phone,
#             client_id=cfg.naver_client_id,
#             client_secret=cfg.naver_client_secret,
#         )
#         if store_info:
#             # store 채우기
#             title = (store_info.get("title") or "").replace("<b>", "").replace("</b>", "")
#             road = store_info.get("roadAddress")
#             ctx.store = StoreInfo(
#                 store_name=title or None,
#                 address=road,
#                 city=(road.split(" ")[0] if road else None),
#                 phone=ctx.extracted.phone,
#                 coords=Coords(x=store_info.get("mapx"), y=store_info.get("mapy")),
#                 naver_raw=(store_info if ctx.mode == "debug" else None),
#             )
#
#     return ctx