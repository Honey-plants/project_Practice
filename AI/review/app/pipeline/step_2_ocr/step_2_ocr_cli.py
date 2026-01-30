from __future__ import annotations

import argparse
from pathlib import Path

from AI.review.app.domain.schemas import PipelineContext
from AI.review.app.pipeline.step_2_ocr.ocr_model import OCRConfig
from AI.review.app.pipeline.step_2_ocr.step_2_ocr import run_step2_ocr


def main():
    p = argparse.ArgumentParser("step2-ocr")
    p.add_argument("image", type=str, help="input image path (rectified or raw)")
    p.add_argument("--out", type=str, default="debug/step2")
    p.add_argument("--no-overlay", action="store_true")
    p.add_argument("--debug", action="store_true", help="save json + keep debug paths")

    args = p.parse_args()

    ctx = PipelineContext(mode="debug" if args.debug else "prod")
    ctx.images.input_path = args.image

    cfg = OCRConfig(
        use_doc_unwarping=False,
        use_textline_orientation=True,
        # det_thresh=0.3,
        # det_box_thresh=0.2,
    )

    # overlay 저장 여부는 runner 인자에 있지만,
    # ctx wrapper는 항상 save_overlay=True로 박혀있으니,
    # 필요하면 run_step2_ocr_to_ctx에 save_overlay 옵션을 추가해도 됨.
    ctx = run_step2_ocr(ctx, out_dir=Path(args.out), cfg=cfg)

    print("✅ n_items:", ctx.ocr.n_items)
    print("✅ overlay:", ctx.ocr.overlay_path)
    if args.debug:
        print("✅ json:", ctx.debug.jsons.get("ocr_result"))


if __name__ == "__main__":
    main()
