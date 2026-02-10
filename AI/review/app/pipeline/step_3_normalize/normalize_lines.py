from __future__ import annotations
from typing import Any, Dict, List


def _y_key(it: Dict[str, Any]) -> int:
    # bbox = [x1, y1, x2, y2]
    x1, y1, x2, y2 = it["bbox"]
    return int((y1 + y2) / 2)  # center_y (기존 y_min 대체)


def normalize_lines(items: List[Dict[str, Any]], y_threshold: int = 10) -> List[str]:

    if not items:
        return []

    items = list(items)

    # 기존처럼 y 기준 정렬 (단, center_y)
    items.sort(key=_y_key)

    lines: List[str] = []
    current: List[Dict[str, Any]] = [items[0]]
    current_y = _y_key(items[0])  #  라인 시작 기준 (고정)

    for it in items[1:]:
        y = _y_key(it)

        if abs(y - current_y) <= y_threshold:
            current.append(it)
        else:
            # 줄 확정
            current.sort(key=lambda z: z["bbox"][0])  # x1 기준
            line = " ".join(t["text"] for t in current if t.get("text"))
            if line.strip():
                lines.append(line.strip())

            # 새 줄 시작
            current = [it]
            current_y = y  #  기준 갱신은 줄이 바뀔 때만 (기존 그대로)

    # 마지막 줄
    current.sort(key=lambda z: z["bbox"][0])
    line = " ".join(t["text"] for t in current if t.get("text"))
    if line.strip():
        lines.append(line.strip())

    return lines
