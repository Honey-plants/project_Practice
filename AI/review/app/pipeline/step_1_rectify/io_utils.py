from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np

def read_bgr(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Failed to read image: {path}")
    return img

def write_image(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), img):
        raise IOError(f"Failed to write image: {path}")

'''
이미지 읽기/쓰기 (역할: I/O 분리)
'''