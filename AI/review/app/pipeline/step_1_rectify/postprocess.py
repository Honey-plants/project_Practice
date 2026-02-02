from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple
import cv2
import numpy as np

@dataclass(frozen=True)
class PostprocessConfig:
    enable: bool = True
    use_clahe: bool = True
    clahe_clip: float = 3.0
    clahe_grid: int = 8
    sharpen: bool = True
    sharpen_strength: float = 0.6   # 0~1
    denoise_strength: int = 3       # 0이면 skip

def postprocess_for_ocr(image_bgr: np.ndarray, cfg: PostprocessConfig) -> Tuple[np.ndarray, Dict[str, Any]]:
    meta: Dict[str, Any] = {"postprocess_for_ocr": asdict(cfg)}
    if not cfg.enable:
        meta["applied"] = False
        return image_bgr, meta

    out = image_bgr

    if cfg.denoise_strength > 0:
        out = cv2.fastNlMeansDenoisingColored(out, None, cfg.denoise_strength, cfg.denoise_strength, 7, 21)

    if cfg.use_clahe:
        lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=float(cfg.clahe_clip), tileGridSize=(int(cfg.clahe_grid), int(cfg.clahe_grid)))
        l2 = clahe.apply(l)
        out = cv2.cvtColor(cv2.merge([l2, a, b]), cv2.COLOR_LAB2BGR)

    if cfg.sharpen and cfg.sharpen_strength > 0:
        # Unsharp mask
        blur = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = cv2.addWeighted(out, 1.0 + float(cfg.sharpen_strength), blur, -float(cfg.sharpen_strength), 0)

    meta["applied"] = True
    return out, meta

'''
OCR 용 보정 ( 텍스트 대비 올리기)
'''