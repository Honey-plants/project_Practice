from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np

@dataclass
class CropResult:
    cropped_bgr: np.ndarray
    quad: Optional[np.ndarray]          # (4,2) float32 or None
    overlay_bgr: np.ndarray             # quad 그려진 이미지
    edges: np.ndarray                   # edge 디버그
    meta: Dict[str, Any]                # find/warp 정보

@dataclass
class PipelineResult:
    final_for_ocr_bgr: np.ndarray
    crop: CropResult
    meta: Dict[str, Any]
