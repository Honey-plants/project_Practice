from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import cv2
import numpy as np

from AI.review.app.pipeline.step_1_rectify.io_utils import read_bgr, write_image  # 이미 있는 유틸 재사용

#처음에 이미지 조금만 보정후 OCR에 보낼 스텝
@dataclass(frozen=True)
class Step0PreprocessConfig:
    enable: bool = True

    # 글자 작은 영수증 체감 큼 (1.5~2.0 추천)
    upscale: float = 1.6  # 1.0이면 skip

    # 조명/대비 개선 (너무 세면 테두리 깨질 수 있어서 중간값)
    use_clahe: bool = True
    clahe_clip: float = 2.5
    clahe_grid: int = 8

    # 노이즈만 살짝 (0이면 skip)
    denoise_strength: int = 3  # 3~5 추천

    # 샤프닝(글자 선명도) - 과하면 링잉 생김
    sharpen: bool = True
    sharpen_amount: float = 0.7  # 0.5~1.0 추천

    # 색 유지할지(기본 유지). 필요하면 grayscale OCR로 바꿀 수도 있음.
    output_gray: bool = False


def _apply_clahe_bgr(img_bgr: np.ndarray, clip: float, grid: int) -> np.ndarray:
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=float(clip), tileGridSize=(int(grid), int(grid)))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)


def _unsharp_mask(img_bgr: np.ndarray, amount: float) -> np.ndarray:
    # amount=0이면 원본과 동일
    if amount <= 0:
        return img_bgr
    blur = cv2.GaussianBlur(img_bgr, (0, 0), 1.0)
    return cv2.addWeighted(img_bgr, 1.0 + float(amount), blur, -float(amount), 0)


def preprocess_for_ocr_basic(
    img_bgr: np.ndarray,
    cfg: Step0PreprocessConfig,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    meta: Dict[str, Any] = {"step0_preprocess": asdict(cfg)}
    if not cfg.enable:
        meta["applied"] = False
        return img_bgr, meta

    out = img_bgr

    # 0) Upscale first (OCR 인식률에 가장 도움)
    if cfg.upscale and cfg.upscale > 1.0:
        h, w = out.shape[:2]
        out = cv2.resize(out, (int(w * cfg.upscale), int(h * cfg.upscale)), interpolation=cv2.INTER_CUBIC)

    # 1) Light denoise (색 유지)
    if cfg.denoise_strength and cfg.denoise_strength > 0:
        s = int(cfg.denoise_strength)
        out = cv2.fastNlMeansDenoisingColored(out, None, s, s, 7, 21)

    # 2) CLAHE (조명/대비 개선)
    if cfg.use_clahe:
        out = _apply_clahe_bgr(out, cfg.clahe_clip, cfg.clahe_grid)

    # 3) Sharpen
    if cfg.sharpen:
        out = _unsharp_mask(out, cfg.sharpen_amount)

    # 4) Optional grayscale
    if cfg.output_gray:
        gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
        out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    meta["applied"] = True
    meta["out_shape"] = list(out.shape)
    return out, meta


def run_step0_preprocess(
    *,
    input_image_path: str,
    out_dir: Path,
    cfg: Step0PreprocessConfig = Step0PreprocessConfig(),
) -> Dict[str, Any]:
    """
    step0: 가벼운 OCR-friendly 전처리만 수행 (warp/crop 없음)
    outputs:
      - 00_input.jpg
      - 10_pre_ocr.jpg
      - meta.json
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    img0 = read_bgr(Path(input_image_path))
    write_image(out_dir / "00_input.jpg", img0)

    img1, meta = preprocess_for_ocr_basic(img0, cfg)
    out_path = out_dir / "10_pre_ocr.jpg"
    write_image(out_path, img1)

    (out_dir / "meta.json").write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "pre_ocr_path": str(out_path),
        "meta": meta,
    }
