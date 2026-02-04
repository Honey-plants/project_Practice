from __future__ import annotations
from typing import Any, Dict, List

def assess_ocr_quality(items: List[Dict[str, Any]], *, low_cut: float = 0.6) -> Dict[str, float]:
    scores = [float(it.get("score", 0.0) or 0.0) for it in items if "score" in it]
    if not scores:
        return {"avg": 0.0, "p10": 0.0, "low_ratio": 1.0, "n": 0}

    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    p10 = scores_sorted[max(0, int(n * 0.10) - 1)]

    low_ratio = sum(s < low_cut for s in scores_sorted) / n
    avg = sum(scores_sorted) / n
    return {"avg": avg, "p10": p10, "low_ratio": low_ratio, "n": n}

def is_bad_quality(q: Dict[str, float]) -> bool:
    # 실무 기본 게이트 (너 상황에 맞게 조절)
    return (q["avg"] < 0.97) or (q["low_ratio"] > 0.20) or (q["n"] < 18)
