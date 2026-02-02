from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, List
import cv2
from AI.review.app.pipeline.step_2_ocr.ocr_model import OCRConfig, get_ocr
from AI.review.app.pipeline.step_2_ocr.ocr_parse import parse_paddleocr_raw
from AI.review.app.pipeline.step_2_ocr.ocr_overlay import draw_poly_overlay


def run_receipt_ocr(
    *,
    image_path: Path,
    out_dir: Path,
    cfg: Optional[OCRConfig] = None,
    save_overlay: bool = True,
    save_json: bool = True,
) -> Dict[str, Any]:
    """
    Step2: OCR only (predict + parse)
    - input: image_path (이미 보정된 이미지)
    - output: payload dict (items 포함)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError(f"Failed to read image: {image_path}")

    if cfg is None:
        cfg = OCRConfig(
            use_doc_unwarping=False,
            use_textline_orientation=True,
        )

    ocr = get_ocr(cfg)
    raw = ocr.predict(image_bgr)
    items: List[Dict[str, Any]] = parse_paddleocr_raw(raw)

    payload: Dict[str, Any] = {
        "image": str(image_path),
        "config": asdict(cfg),
        "n_items": len(items),
        "items": items,
        "outputs": {},
    }

    if save_overlay:
        overlay = draw_poly_overlay(image_bgr, items)
        overlay_path = out_dir / "ocr_overlay.jpg"
        cv2.imwrite(str(overlay_path), overlay)
        payload["outputs"]["overlay"] = str(overlay_path)

    if save_json:
        import json
        json_path = out_dir / "ocr_result.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["outputs"]["json"] = str(json_path)

    return payload
