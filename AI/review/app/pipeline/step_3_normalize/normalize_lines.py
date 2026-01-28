from __future__ import annotations
from typing import Any, Dict, List, Tuple


def _y_key(it: Dict[str, Any]) -> int:
    # bbox = [x1,y1,x2,y2]
    x1, y1, x2, y2 = it["bbox"]
    return int((y1 + y2) / 2)  # ✅ y_min 대신 center가 더 안정적


def normalize_lines(items: List[Dict[str, Any]], y_threshold: int = 15) -> List[str]:
    """
    items(bbox/poly 기반) -> 라인 문자열 리스트
    """
    if not items:
        return []

    items = list(items)
    items.sort(key=_y_key)

    lines: List[str] = []
    current: List[Dict[str, Any]] = [items[0]]
    current_y = _y_key(items[0])

    for it in items[1:]:
        y = _y_key(it)
        if abs(y - current_y) <= y_threshold:
            current.append(it)
        else:
            current.sort(key=lambda z: z["bbox"][0])  # x1 기준
            lines.append(" ".join(t["text"] for t in current if t["text"]))
            current = [it]
            current_y = y

    current.sort(key=lambda z: z["bbox"][0])
    lines.append(" ".join(t["text"] for t in current if t["text"]))

    # 빈 줄 제거
    return [ln.strip() for ln in lines if ln.strip()]
