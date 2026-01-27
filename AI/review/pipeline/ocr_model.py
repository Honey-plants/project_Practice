# AI/review/pipeline/ocr_model.py

import os
from typing import Optional


# Lazy singleton
_ocr_model = None  # type: Optional[object]

def get_ocr_model():
    """
    PaddleOCR 모델을 '요청 시점'에 1회만 로딩하는 Lazy Loader.
    API 부팅(import) 단계에서 Paddle/PaddleOCR 로딩을 피하기 위한 목적.
    """
    global _ocr_model


    # 운영에서 OCR을 아예 끄고 싶을 때(예: API/Worker 분리 전)
    if os.getenv("DISABLE_OCR", "false").lower() in ("1", "true", "yes"):
        raise RuntimeError("OCR is disabled by DISABLE_OCR=true")

    if _ocr_model is not None:
        return _ocr_model

    # Paddle/PaddleOCR import 자체가 무겁고 OS 의존성이 있으므로 여기서 import
    from paddleocr import PaddleOCR  # noqa

    print("🔥 Loading OCR model once (lazy)...")

    _ocr_model = PaddleOCR(
        lang="korean",
        use_textline_orientation=True,
        use_doc_unwarping=False,
        text_det_limit_side_len=1280,
        text_det_thresh=0.3,
        text_det_box_thresh=0.2,
        text_det_unclip_ratio=1.5,
        enable_mkldnn=False,
    )

    return _ocr_model
