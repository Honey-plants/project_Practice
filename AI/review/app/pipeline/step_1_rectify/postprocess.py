from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple
import cv2
import numpy as np

@dataclass(frozen=True)
class PostprocessConfig:
    enable: bool = True

    # Prefer gray-based processing for receipts
    denoise_strength: int = 0      # 0이면 skip
    use_clahe: bool = False
    clahe_clip: float = 2.0         # 낮춤 (기존 3.0)
    clahe_grid: int = 8

    upscale: float = 1.8  # 1.0이면 skip

    # Brightness protection
    preserve_brightness: bool = True
    max_dark_drop: float = 0.03     # 평균 밝기 6% 이상 떨어지면 보정
    gamma: float = 0.85             # <1 이면 밝아짐 (0.85~0.95 추천)

    sharpen: bool = True
    sharpen_strength: float = 0.35  # 낮춤 (기존 0.6)

def _apply_gamma_u8(img_bgr: np.ndarray, gamma: float) -> np.ndarray:
    # gamma < 1 => brighter, gamma > 1 => darker
    if gamma <= 0:
        return img_bgr
    table = (np.linspace(0, 1, 256) ** gamma * 255.0).astype(np.uint8)
    return cv2.LUT(img_bgr, table)

def postprocess_for_ocr(image_bgr: np.ndarray, cfg: PostprocessConfig) -> Tuple[np.ndarray, Dict[str, Any]]:
    meta: Dict[str, Any] = {"postprocess_for_ocr": asdict(cfg)}
    if not cfg.enable:
        meta["applied"] = False
        return image_bgr, meta

    out = image_bgr.copy()

    # --- measure brightness before (use LAB L mean) ---
    lab0 = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    L0 = lab0[:, :, 0]
    mean0 = float(np.mean(L0))
    meta["mean_L_before"] = mean0

    # 0) Upscale first (OCR 인식률에 가장 도움)
    if cfg.upscale and cfg.upscale > 1.0:
        h, w = out.shape[:2]
        out = cv2.resize(out, (int(w * cfg.upscale), int(h * cfg.upscale)), interpolation=cv2.INTER_CUBIC)

    # 1) Denoise (gray-based is usually better for receipts)
    if cfg.denoise_strength > 0:
        gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
        gray_dn = cv2.fastNlMeansDenoising(gray, None, cfg.denoise_strength, 7, 21)
        out = cv2.cvtColor(gray_dn, cv2.COLOR_GRAY2BGR)

    # 2) CLAHE on L channel (or gray), but gentle
    if cfg.use_clahe:
        lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
        L, A, B = cv2.split(lab)
        clahe = cv2.createCLAHE(
            clipLimit=float(cfg.clahe_clip),
            tileGridSize=(int(cfg.clahe_grid), int(cfg.clahe_grid)),
        )
        L2 = clahe.apply(L)
        out = cv2.cvtColor(cv2.merge([L2, A, B]), cv2.COLOR_LAB2BGR)

    # --- measure brightness after clahe ---
    lab1 = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    mean1 = float(np.mean(lab1[:, :, 0]))
    meta["mean_L_after_clahe"] = mean1

    # 3) Brightness preservation (gamma lift if it got darker)
    if cfg.preserve_brightness:
        drop = (mean0 - mean1) / max(mean0, 1e-6)
        meta["brightness_drop_ratio"] = float(drop)

        if drop > cfg.max_dark_drop:
            # brighten a bit
            out = _apply_gamma_u8(out, cfg.gamma)
            meta["gamma_applied"] = cfg.gamma
        else:
            meta["gamma_applied"] = None

    # 4) Sharpen (keep mild)
    if cfg.sharpen and cfg.sharpen_strength > 0:
        blur = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = cv2.addWeighted(out, 1.0 + float(cfg.sharpen_strength), blur, -float(cfg.sharpen_strength), 0)
        out = np.clip(out, 0, 255).astype(np.uint8)

    meta["applied"] = True
    return out, meta
