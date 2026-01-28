from __future__ import annotations
from typing import Any, Dict, List
import cv2
import numpy as np

def draw_poly_overlay(image_bgr: np.ndarray, items: List[Dict[str, Any]]) -> np.ndarray:
    vis = image_bgr.copy()
    for it in items:
        poly = it.get("poly")
        if not poly or len(poly) != 4:
            continue
        pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(vis, [pts], True, (0, 255, 0), 2)
    return vis
