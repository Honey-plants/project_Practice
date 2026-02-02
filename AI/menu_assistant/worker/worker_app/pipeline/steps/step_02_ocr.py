from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from menu_assistant.worker.worker_app.vision.rectify import read_image_bgr
from menu_assistant.worker.worker_app.ocr.paddle_runner import (
    parse_paddleocr_raw,
    run_paddleocr,
    write_vis_image,
)
from menu_assistant.worker.worker_app.pipeline.steps.config import (default_data_dir_from_steps_file)


# Optional preprocess (pixel-only, geometry-invariant)
try:
    from AI.preprocess_korean_menu import PreprocessConfig, preprocess_menu_image
except Exception:
    try:
        from preprocess_korean_menu import PreprocessConfig, preprocess_menu_image
    except Exception:
        PreprocessConfig = None  # type: ignore
        preprocess_menu_image = None  # type: ignore


# -----------------------------
# Path resolving (run folder)
# -----------------------------

def resolve_rectified_from_run(data_dir: Path, run_id: str, run_dir: Optional[Path] = None) -> Path:
    """Step1 output convention (backward compatible):
      - if run_dir provided: <run_dir>/rectify/rectified.jpg
      - else              : <data_dir>/runs/<run_id>/rectify/rectified.jpg
    """

    if run_dir is not None:
        p = run_dir / "rectify" / "rectified.jpg"
    else:
        p = data_dir / "runs" / run_id / "rectify" / "rectified.jpg"
    if not p.exists():
        raise FileNotFoundError(f"Rectified image not found: {p}")
    return p


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 02 - PaddleOCR (uses rectified image; outputs OCR json only; normalization in Step03)"
    )

    # Choose ONE: run_id (recommended) OR direct image path
    parser.add_argument(
        "--run_id",
        default=None,
        help="Run id from Step1 (reads <data_dir>/runs/<run_id>/rectify/rectified.jpg)",
    )
    parser.add_argument("--data_dir", default="menu_assistant/data", help="Base data directory (contains runs/)")
    parser.add_argument("--run_dir", default=None, help="Optional run directory override (tmp/.../ai_runs/<run_id>)")
    parser.add_argument("--image", default=None, help="Direct path to rectified image (if not using --run_id)")

    # Output
    parser.add_argument("--out", default=None, help="Output json path. Default: <run>/ocr/ocr.json")
    parser.add_argument("--vis", default=None, help="Optional vis image path. Default: <run>/ocr/ocr_vis.jpg")
    parser.add_argument("--dump_raw", action="store_true", help="Save raw preview for debugging")

    # OCR params
    parser.add_argument("--lang", default="korean")
    parser.add_argument("--det_limit_side_len", type=int, default=4000)
    parser.add_argument("--det_limit_type", default="max")

    # DET tuning (optional)
    parser.add_argument("--det_box_thresh", type=float, default=None)
    parser.add_argument("--det_thresh", type=float, default=None)
    parser.add_argument("--det_unclip_ratio", type=float, default=None)

    # Keep "auto correction" OFF by default
    parser.add_argument(
        "--use_doc_unwarping", action="store_true", help="(Optional) enable doc unwarping if supported"
    )
    parser.add_argument(
        "--use_textline_orientation",
        action="store_true",
        help="(Optional) enable textline orientation if supported",
    )

    # Custom model dirs (optional)
    parser.add_argument("--det_model_dir", default=None)
    parser.add_argument("--rec_model_dir", default=None)
    parser.add_argument("--cls_model_dir", default=None)

    # Optional preprocess (pixel-only)
    parser.add_argument("--use_preprocess", action="store_true", help="Apply preprocess_korean_menu (pixel-only)")
    parser.add_argument("--preprocess_mode", default="clahe_denoise_sharp")

    args = parser.parse_args()

    # data_dir 보정: 기존 default 문자열 유지 + repo 기준 fallback
    data_dir = Path(args.data_dir) if args.data_dir else default_data_dir_from_steps_file(__file__)
    run_dir = Path(args.run_dir) if args.run_dir else None

    # Resolve input image
    if args.image:
        img_path = Path(args.image)
        if not img_path.exists():
            raise FileNotFoundError(f"--image not found: {img_path}")
        run_base = None
    else:
        if not args.run_id:
            raise RuntimeError("Provide either --run_id or --image.")
        img_path = resolve_rectified_from_run(data_dir=data_dir, run_id=args.run_id, run_dir=run_dir)
        run_base = run_dir if run_dir is not None else (data_dir / "runs" / args.run_id)

    # Output paths
    if args.out:
        out_json = Path(args.out)
    else:
        out_json = (Path.cwd() / "ocr.json") if run_base is None else (run_base / "ocr" / "ocr.json")

    if args.vis:
        out_vis = Path(args.vis)
    else:
        out_vis = None if run_base is None else (run_base / "ocr" / "ocr_vis.jpg")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    if out_vis is not None:
        out_vis.parent.mkdir(parents=True, exist_ok=True)

    # Load image (BGR)
    img_bgr = read_image_bgr(str(img_path))

    # Optional preprocess (pixel-only)
    preprocess_meta: Dict[str, Any] = {"preprocess": {"enabled": False}}
    if args.use_preprocess:
        if PreprocessConfig is None or preprocess_menu_image is None:
            raise ImportError(
                "preprocess_korean_menu.py import failed. Check module path: AI/preprocess_korean_menu.py"
            )
        cfg = PreprocessConfig(mode=args.preprocess_mode, output="bgr")
        img_bgr = preprocess_menu_image(img_bgr, cfg)
        preprocess_meta = {
            "preprocess": {
                "enabled": True,
                "mode": args.preprocess_mode,
                "method": "geometry_invariant_pixel_only",
            }
        }

    # Run OCR
    t0 = time.time()
    raw = run_paddleocr(
        image_path=img_path,
        image_bgr=img_bgr,
        lang=args.lang,
        det_limit_side_len=args.det_limit_side_len,
        det_limit_type=args.det_limit_type,
        use_doc_unwarping=bool(args.use_doc_unwarping),
        use_textline_orientation=bool(args.use_textline_orientation),
        det_model_dir=args.det_model_dir,
        rec_model_dir=args.rec_model_dir,
        cls_model_dir=args.cls_model_dir,
        det_box_thresh=args.det_box_thresh,
        det_thresh=args.det_thresh,
        det_unclip_ratio=args.det_unclip_ratio,
    )
    items = parse_paddleocr_raw(raw)
    elapsed_ms = int((time.time() - t0) * 1000)

    # Save JSON: OCR output only (normalization happens in Step03)
    result: Dict[str, Any] = {
        "image": str(img_path),
        "image_shape": [int(img_bgr.shape[0]), int(img_bgr.shape[1])],
        "engine": "paddleocr",
        "elapsed_ms": elapsed_ms,
        "paddleocr_config": {
            "lang": args.lang,
            "det_limit_side_len": int(args.det_limit_side_len),
            "det_limit_type": str(args.det_limit_type),
            "det_box_thresh": args.det_box_thresh,
            "det_thresh": args.det_thresh,
            "det_unclip_ratio": args.det_unclip_ratio,
            "use_doc_unwarping": bool(args.use_doc_unwarping),
            "use_textline_orientation": bool(args.use_textline_orientation),
            "det_model_dir": args.det_model_dir,
            "rec_model_dir": args.rec_model_dir,
            "cls_model_dir": args.cls_model_dir,
        },
        "items": items,
        "notes": "Rectified image is treated as source. Text normalization/menu policy is handled in Step03.",
    }
    result.update(preprocess_meta)

    if args.dump_raw:
        try:
            result["_raw_type"] = type(raw).__name__
            result["_raw_preview"] = repr(raw)[:5000]
        except Exception:
            result["_raw_preview"] = "<raw_preview_failed>"

    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Optional visualization
    if out_vis is not None:
        write_vis_image(out_vis, img_bgr, items)

    print(f"[OK] items={len(items)} elapsed_ms={elapsed_ms}")
    print(f"[OK] json={out_json}")
    if out_vis is not None:
        print(f"[OK] vis={out_vis}")


if __name__ == "__main__":
    main()
