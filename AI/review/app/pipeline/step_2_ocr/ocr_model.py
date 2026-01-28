from __future__ import annotations

import inspect
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


#OCR 파라미터를 한곳에 모은 설정 클래스
@dataclass
class OCRConfig:
    lang: str = "korean"                    #모델에 사용할 언어모델

    #features
    use_textline_orientation: bool = True   #텍스트 줄 단위 방향 보정
    use_doc_unwarping: bool = False         #문서 굴곡 보정
    enable_mkldnn: bool = False             #CPU 가속옵션 (windows에서는 크래시 원인->꺼야함)
    show_log: bool = False                  #내부로그 출력여부

    #DET resize
    det_limit_side_len: int = 1280 #이미지 사이즈 resize (크면 정확도UP, 속도 DOWN)
    det_limit_type: str = "max"

    # DET thresholds (DB-style)
    det_thresh: float = 0.3                 #픽셀단위에서 "글자일 확률"기준 (낮추면 흐린글씨도 검출됨)
    det_box_thresh: float = 0.2             #박스단위 confidence (낮추면 박스가 많아짐)
    det_unclip_ratio: float = 1.5           #검출된 텔스트 영역을 얼마나 확장할지(글자가 박스 밖으로 잘리는것 방지)

    # optional model dirs
    det_model_dir: Optional[str] = None     #직접학습한 DET 모델경로
    rec_model_dir: Optional[str] = None     #문자인식 모델 경로
    cls_model_dir: Optional[str] = None     #방향 분류 모델 경로

def import_paddleocr():
    from paddleocr import PaddleOCR  # type: ignore
    return PaddleOCR

#파라미터 이름 자동 매핑: 다른버전의 파라미터 이름 차이를 해결하는 함수
def _apply_first_supported(kwargs: Dict[str, Any], supported: set, value: Any, *names: str) -> None:
    """Set kwargs[name] = value for the first name that exists in supported."""
    for n in names:
        if n in supported:
            kwargs[n] = value
            return

#설정 객체를 받아 OCR 엔진을 생성
def build_paddleocr(config: OCRConfig) -> Any:
    PaddleOCR = import_paddleocr()

    sig = inspect.signature(PaddleOCR.__init__)
    supported = set(sig.parameters.keys())

    kwargs: Dict[str, Any] = {}             #최종 OCR 셍성자에 넘길 인자들

    # ---- common / stable ----
    _apply_first_supported(kwargs, supported, config.lang, "lang")
    _apply_first_supported(kwargs, supported, bool(config.show_log), "show_log")
    _apply_first_supported(kwargs, supported, bool(config.enable_mkldnn), "enable_mkldnn")

    # Features (3.2.2 uses these exact names)
    _apply_first_supported(kwargs, supported, bool(config.use_textline_orientation), "use_textline_orientation")
    _apply_first_supported(kwargs, supported, bool(config.use_doc_unwarping), "use_doc_unwarping")

    # DET resize: support both styles
    _apply_first_supported(
        kwargs, supported, int(config.det_limit_side_len),
        "text_det_limit_side_len", "det_limit_side_len"
    )
    _apply_first_supported(
        kwargs, supported, str(config.det_limit_type),
        "text_det_limit_type", "det_limit_type"
    )

    # DET thresholds: support 3.2.2 prefix AND other variants
    _apply_first_supported(
        kwargs, supported, float(config.det_thresh),
        "text_det_thresh", "text_det_db_thresh", "det_thresh", "det_db_thresh"
    )
    _apply_first_supported(
        kwargs, supported, float(config.det_box_thresh),
        "text_det_box_thresh", "text_det_db_box_thresh", "det_box_thresh", "det_db_box_thresh"
    )
    _apply_first_supported(
        kwargs, supported, float(config.det_unclip_ratio),
        "text_det_unclip_ratio", "text_det_db_unclip_ratio", "det_unclip_ratio", "det_db_unclip_ratio"
    )

    # optional model dirs
    if config.det_model_dir:
        _apply_first_supported(kwargs, supported, config.det_model_dir, "det_model_dir")
    if config.rec_model_dir:
        _apply_first_supported(kwargs, supported, config.rec_model_dir, "rec_model_dir")
    if config.cls_model_dir:
        _apply_first_supported(kwargs, supported, config.cls_model_dir, "cls_model_dir")

    return PaddleOCR(**kwargs)                  #모델생성


# -----------------------------
# Singleton 모델 1번만 로딩
# -----------------------------
_ocr_singleton = None
_loaded_config: Optional[OCRConfig] = None


def get_ocr(config: Optional[OCRConfig] = None) -> Any:
    """
    Returns a process-level singleton OCR model.
    If you pass a new config different from the loaded one, it will rebuild.
    """
    global _ocr_singleton, _loaded_config

    if config is None:
        config = OCRConfig()

    if _ocr_singleton is None or _loaded_config is None or asdict(config) != asdict(_loaded_config):
        print("🔥 Loading OCR model...", config)
        _ocr_singleton = build_paddleocr(config)
        _loaded_config = config

    return _ocr_singleton