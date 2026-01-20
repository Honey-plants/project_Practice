"""OCR bbox post-processing (merge/sort/clean).

This module owns:
- Parsing raw PaddleOCR outputs into a stable schema
- Lightweight text normalization suitable for downstream normalize step
- Optional visualization helpers
- Saving of OCR json payloads (so step_02_ocr stays execution-only)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np


def parse_paddleocr_raw(raw: Any) -> List[Dict[str, Any]]:
    """Normalize PaddleOCR outputs into:
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
        if len(raw) == 1 and isinstance(raw[0], list):
            raw = raw[0]

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


_WS_RE = re.compile(r"\s+")
_TRIM_BAD_EDGE_RE = re.compile(r"^[\s\|\-·•]+|[\s\|\-·•]+$")


def simple_normalize_text(s: str) -> str:
    """Lightweight normalization for OCR tokens.

    Intentionally conservative (geometry/semantics safe):
    - strip
    - collapse whitespace
    - trim obvious edge punctuations used as list separators
    """

    s = str(s)
    s = _WS_RE.sub(" ", s).strip()
    s = _TRIM_BAD_EDGE_RE.sub("", s).strip()
    return s


def simple_normalize_items(items: List[Dict[str, Any]], *, drop_empty: bool = True) -> List[Dict[str, Any]]:
    """Apply simple_normalize_text to each item's text."""

    out: List[Dict[str, Any]] = []
    for it in items:
        t0 = it.get("text", "")
        t1 = simple_normalize_text(t0)
        if drop_empty and not t1:
            continue
        new_it = dict(it)
        new_it["text_raw"] = t0
        new_it["text"] = t1
        out.append(new_it)
    return out


def draw_vis(image_bgr: np.ndarray, items: List[Dict[str, Any]]) -> np.ndarray:
    vis = image_bgr.copy()
    for it in items:
        poly = it.get("poly")
        if not poly or len(poly) != 4:
            continue
        pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(vis, [pts], True, (0, 255, 0), 2)
    return vis


def write_result_json(out_json: Path, result: Dict[str, Any]) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def write_vis_image(out_vis: Path, image_bgr: np.ndarray, items: List[Dict[str, Any]]) -> None:
    out_vis.parent.mkdir(parents=True, exist_ok=True)
    vis = draw_vis(image_bgr, items)
    # BGR write via OpenCV
    cv2.imwrite(str(out_vis), vis)
