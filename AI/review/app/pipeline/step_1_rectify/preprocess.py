from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple
import cv2
import numpy as np

@dataclass(frozen=True)
class PreprocessConfig:
    enable: bool = True
    # 밝기/그림자 완화 (너무 강하게 하면 테두리 왜곡됨)
    use_clahe: bool = True
    clahe_clip: float = 2.0
    clahe_grid: int = 8
    # 노이즈만 살짝
    denoise_strength: int = 5  # 0이면 skip

def preprocess_for_crop(image_bgr: np.ndarray, cfg: PreprocessConfig) -> Tuple[np.ndarray, Dict[str, Any]]:
    meta: Dict[str, Any] = {"preprocess_for_crop": asdict(cfg)}
    if not cfg.enable:
        meta["applied"] = False
        return image_bgr, meta

    out = image_bgr

    # 1) 약한 denoise (색 유지)
    if cfg.denoise_strength > 0:
        out = cv2.fastNlMeansDenoisingColored(out, None, cfg.denoise_strength, cfg.denoise_strength, 7, 21)

    # 2) CLAHE (명암 대비 개선 - edge 도움)
    if cfg.use_clahe:
        lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=float(cfg.clahe_clip), tileGridSize=(int(cfg.clahe_grid), int(cfg.clahe_grid)))
        l2 = clahe.apply(l)
        lab2 = cv2.merge([l2, a, b])
        out = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)

    meta["applied"] = True
    return out, meta

'''
크롭전 보정 => 영수증 테두리 코너 탐지 도움
'''