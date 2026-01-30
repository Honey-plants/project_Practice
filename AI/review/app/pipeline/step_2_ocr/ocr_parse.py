from __future__ import annotations
from typing import Any, Dict, List

# -----------------------------
# 결과 파싱 (PaddleOCR raw -> items)
# -----------------------------
def parse_paddleocr_raw(raw: Any) -> List[Dict[str, Any]]:
    """
    PaddleOCR output을 안정적인 schema로 변환:
      [{text, score, poly(4pts), bbox[x1,y1,x2,y2]}, ...]
    PaddleOCR 버전에 따라 raw 구조가 달라서 방어적으로 처리.
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

    # dict wrapper
    if isinstance(raw, dict):
        for k in ("results", "res", "result", "data", "lines"):
            v = raw.get(k)
            if isinstance(v, list):
                return parse_paddleocr_raw(v)
        return items

    # list wrapper
    if isinstance(raw, list):
        # sometimes [[...]] wrapper
        if len(raw) == 1 and isinstance(raw[0], list):
            raw = raw[0]

        # list[dict] 형태
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

        # classic: [poly, (text, score)]
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

