import argparse
from pathlib import Path

from AI.review.app.pipeline.step_1_rectify.step_1_rectify import run_step1_rectify
from AI.review.app.pipeline.step_1_rectify.run_rectify import run_receipt_rectify, RectifyConfig


def main():
    p = argparse.ArgumentParser(prog="step1-rectify")
    p.add_argument("image", type=str, help="input receipt image path")
    p.add_argument("--out", type=str, default="debug_out", help="output debug folder")

    # (optional) tuning knobs from CLI
    p.add_argument("--blur", type=int, default=5)
    p.add_argument("--dilate", type=int, default=2)
    p.add_argument("--eps", type=float, default=0.06)
    p.add_argument("--min-area", type=float, default=0.03)
    p.add_argument("--canny1", type=int, default=40)
    p.add_argument("--canny2", type=int, default=150)

    args = p.parse_args()

    cfg = RectifyConfig()
    cfg.crop = cfg.crop.__class__(
        blur_ksize=args.blur,
        dilate_iter=args.dilate,
        approx_eps_ratio=args.eps,
        min_area_ratio=args.min_area,
        canny1=args.canny1,
        canny2=args.canny2,
    )
    out_dir = Path(args.out)
    res = run_receipt_rectify(
        image_path=Path(args.image),
        out_dir=out_dir,
        cfg=cfg,
    )

    found = res.meta["crop"]["find"]["found"]
    print("found_receipt:", found)
    print("output_dir:", out_dir.resolve())


if __name__ == "__main__":
    main()
