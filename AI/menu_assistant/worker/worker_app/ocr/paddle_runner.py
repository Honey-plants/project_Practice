from __future__ import annotations

"""PaddleOCR runner (configuration/engine side).

This module owns ONLY engine-facing logic:
- Safe PaddleOCR construction (signature-aware)
- OCR execution with robust fallback (predict -> ocr)
- Parsing raw outputs into a stable schema (items: text/score/poly/bbox)
- Optional visualization helper

Policy/normalization of menu text is handled in Step 03 (step_03_normalize).
"""

import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np


# -----------------------------
# PaddleOCR safe construction
# -----------------------------

def import_paddleocr():
    try:
        from paddleocr import PaddleOCR  # type: ignore
        return PaddleOCR
    except Exception as e:
        raise RuntimeError(
            "PaddleOCR import failed. Your environment may be broken or missing dependencies.\n"
            "Try reinstalling on a clean venv.\n"
            "\nInstall (CPU) example:\n"
            "  pip install -U pip\n"
            "  pip install paddlepaddle\n"
            "  pip install paddleocr\n"
            "  pip install opencv-python numpy\n"
        ) from e


def build_paddleocr(
    PaddleOCR_cls: Any,
    *,
    lang: str,
    det_limit_side_len: int,
    det_limit_type: str,
    use_doc_unwarping: bool,
    use_textline_orientation: bool,
    det_model_dir: Optional[str] = None,
    rec_model_dir: Optional[str] = None,
    cls_model_dir: Optional[str] = None,
    det_box_thresh: Optional[float] = None,
    det_thresh: Optional[float] = None,
    det_unclip_ratio: Optional[float] = None,
) -> Any:
    sig = inspect.signature(PaddleOCR_cls.__init__)
    supported = set(sig.parameters.keys())

    kwargs: Dict[str, Any] = {}

    if "lang" in supported:
        kwargs["lang"] = lang

    if "det_limit_side_len" in supported:
        kwargs["det_limit_side_len"] = int(det_limit_side_len)
    if "det_limit_type" in supported:
        kwargs["det_limit_type"] = str(det_limit_type)

    # Explicitly disable optional features unless enabled
    if "use_doc_unwarping" in supported:
        kwargs["use_doc_unwarping"] = bool(use_doc_unwarping)
    if "use_textline_orientation" in supported:
        kwargs["use_textline_orientation"] = bool(use_textline_orientation)

    # DET tuning (only if supported by installed PaddleOCR)
    if det_box_thresh is not None and "det_box_thresh" in supported:
        kwargs["det_box_thresh"] = float(det_box_thresh)
    if det_thresh is not None and "det_thresh" in supported:
        kwargs["det_thresh"] = float(det_thresh)
    if det_unclip_ratio is not None and "det_unclip_ratio" in supported:
        kwargs["det_unclip_ratio"] = float(det_unclip_ratio)

    # optional model dirs
    if det_model_dir and "det_model_dir" in supported:
        kwargs["det_model_dir"] = det_model_dir
    if rec_model_dir and "rec_model_dir" in supported:
        kwargs["rec_model_dir"] = rec_model_dir
    if cls_model_dir and "cls_model_dir" in supported:
        kwargs["cls_model_dir"] = cls_model_dir

    return PaddleOCR_cls(**kwargs)


# -----------------------------
# OCR run + robust parsing
# -----------------------------

def ocr_predict_or_ocr(ocr: Any, image_path: Path, image_bgr: np.ndarray) -> Any:
    """Run OCR with robust fallback.

    Priority:
      1) predict(path)
      2) predict(ndarray BGR)
      3) ocr(path)
      4) ocr(ndarray BGR)

    Note: Do NOT convert to RGB here.
    """

    raw = None

    if hasattr(ocr, "predict") and callable(getattr(ocr, "predict")):
        try:
            raw = ocr.predict(str(image_path))
            return raw
        except Exception:
            raw = None

        try:
            raw = ocr.predict(image_bgr)
            return raw
        except Exception:
            raw = None

    if hasattr(ocr, "ocr") and callable(getattr(ocr, "ocr")):
        try:
            raw = ocr.ocr(str(image_path))
            return raw
        except Exception:
            raw = None

        raw = ocr.ocr(image_bgr)

    return raw


def run_paddleocr(
    *,
    image_path: Path,
    image_bgr: np.ndarray,
    lang: str,
    det_limit_side_len: int,
    det_limit_type: str,
    use_doc_unwarping: bool,
    use_textline_orientation: bool,
    det_model_dir: Optional[str] = None,
    rec_model_dir: Optional[str] = None,
    cls_model_dir: Optional[str] = None,
    det_box_thresh: Optional[float] = None,
    det_thresh: Optional[float] = None,
    det_unclip_ratio: Optional[float] = None,
) -> Any:
    PaddleOCR = import_paddleocr()
    ocr = build_paddleocr(
        PaddleOCR,
        lang=lang, #언어(korean)
        det_limit_side_len=det_limit_side_len,#DET 전에 이미지의 긴변을 이 값으로 리사이즈
        det_limit_type=det_limit_type,#det_limit_side_len을 어떤 기준으로 적용할지 결정
        use_doc_unwarping=use_doc_unwarping,#PaddleOCR 내부의 문서 펼침(unwarping) 기능 사용 여부
        use_textline_orientation=use_textline_orientation,#텍스트 라인이 뒤집혀 있는지 판단할지 여부
        det_model_dir=det_model_dir,#텍스트 검출(DET) 모델 디렉터리
        rec_model_dir=rec_model_dir,#실제 문자열 인식 모델 경로
        cls_model_dir=cls_model_dir,#텍스트 방향(0° / 180°) 분류 모델 경로
        det_box_thresh=det_box_thresh,#텍스트 박스로 채택할 최소 confidence
        det_thresh=det_thresh,#픽셀 단위에서 “글자일 가능성” 판정 기준
        det_unclip_ratio=det_unclip_ratio,#검출된 텍스트 영역을 얼마나 확장(unclip) 할지
    )
    return ocr_predict_or_ocr(ocr, image_path, image_bgr)


def parse_paddleocr_raw(raw: Any) -> List[Dict[str, Any]]:
    """Normalize PaddleOCR outputs into a stable list of items.

    Output:
      [{text, score, poly(4pts), bbox[x1,y1,x2,y2]}, ...]

    Supports:
      A) PaddleX-style dict in list: {'rec_texts','rec_scores','rec_polys'/'dt_polys'}
      B) list[dict] item-wise: {'text','points','score'}
      C) classic: [poly, (text, score)]
      D) dict wrapper with list under res/result/results/data/lines
    """

    items: List[Dict[str, Any]] = []

    def add_item(text: str, score: float, poly_pts) -> None:
        pts = poly_pts
        if hasattr(pts, "tolist"):
            pts = pts.tolist()
        pts_i = [[int(p[0]), int(p[1])] for p in pts]
        xs = [p[0] for p in pts_i]
        ys = [p[1] for p in pts_i]
        bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
        items.append({"text": str(text), "score": float(score), "poly": pts_i, "bbox": bbox})

    if raw is None:
        return items

    if isinstance(raw, dict):
        for k in ("results", "res", "result", "data", "lines"):
            v = raw.get(k)
            if isinstance(v, list):
                return parse_paddleocr_raw(v)
        return items

    if isinstance(raw, list):
        # unwrap page wrapper
        if len(raw) == 1 and isinstance(raw[0], list):
            raw = raw[0]

        # Case A/B: list[dict]
        if len(raw) > 0 and isinstance(raw[0], dict):
            for d in raw:
                rec_texts = d.get("rec_texts")
                rec_scores = d.get("rec_scores")
                rec_polys = d.get("rec_polys") or d.get("dt_polys")

                if isinstance(rec_texts, list) and isinstance(rec_scores, list) and isinstance(rec_polys, list):
                    n = min(len(rec_texts), len(rec_scores), len(rec_polys))
                    for i in range(n):
                        add_item(rec_texts[i], float(rec_scores[i]), rec_polys[i])
                    continue

                txt = d.get("text") or d.get("rec_text") or d.get("transcription")
                sc = d.get("confidence") or d.get("score") or d.get("rec_score") or 1.0
                pts = d.get("points") or d.get("poly") or d.get("bbox")
                if txt is not None and pts is not None:
                    if hasattr(pts, "tolist"):
                        pts = pts.tolist()
                    if isinstance(pts, list) and len(pts) == 4:
                        add_item(str(txt), float(sc), pts)

            return items

        # Case C: classic [poly, (text, score)]
        for entry in raw:
            try:
                if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                    continue
                poly, rec = entry
                if hasattr(poly, "tolist"):
                    poly = poly.tolist()
                if not (isinstance(poly, (list, tuple)) and len(poly) == 4):
                    continue

                if isinstance(rec, (list, tuple)) and len(rec) >= 2:
                    txt, sc = rec[0], float(rec[1])
                elif isinstance(rec, dict):
                    txt = rec.get("text") or rec.get("rec_text")
                    sc = float(rec.get("score", 1.0))
                else:
                    continue

                add_item(str(txt), float(sc), poly)
            except Exception:
                continue

    return items


def draw_vis(image_bgr: np.ndarray, items: List[Dict[str, Any]]) -> np.ndarray:
    vis = image_bgr.copy()
    for it in items:
        poly = it.get("poly")
        if not poly or len(poly) != 4:
            continue
        pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(vis, [pts], True, (0, 255, 0), 2)
    return vis


def write_vis_image(out_path: Path, image_bgr: np.ndarray, items: List[Dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), draw_vis(image_bgr, items))
