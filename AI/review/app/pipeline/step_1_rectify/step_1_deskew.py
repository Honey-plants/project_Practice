from pathlib import Path
from typing import Any, Dict, List, Tuple
import cv2
import json

from .deskew_utils import deskew_image_using_ocr_or_hough  # (내가 준 함수)

def run_step1_deskew(*, image_path: str, ocr_items: List[Dict[str, Any]], out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to read image: {image_path}")

    rotated, skew, method = deskew_image_using_ocr_or_hough(img, ocr_items)

    out_path = out_dir / "deskew.png"
    cv2.imwrite(str(out_path), rotated)

    meta = {"skew_deg": skew, "method": method, "out_path": str(out_path)}
    (out_dir / "deskew_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
