from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ============================================================
# Step 03: Normalize menu strings (Korean-only) + keep poly
#
# STABILIZED MERGE:
# - 2-pass merge within each text line (y-cluster)
#   Pass1: merge ONLY short Hangul fragments (len 1~2)
#   Pass2: conditional merge for longer fragments, with strict guards
# - Stop merge when next token looks like PRICE/NUMBER column (digits/"원")
# - Use both absolute x-gap and relative x-gap (gap / avg_height)
# - Split by "/" AFTER merge, BEFORE normalize
#
# Final output keeps ONLY:
#   { raw_menu, poly, menu_norm }
# ============================================================


_NON_MENU_HARD_KEYWORDS = [
    "원산지", "국내산", "수입산",
    "포장", "배달", "환불", "결제",
    "문의", "전화",
    "알레르기", "알러지", "주의",
]

_NON_MENU_TITLES = {
    "안주", "사이드", "추가", "추가메뉴", "사리", "음료", "음료수", "주류", "메뉴",
}

_KEEP_HANGUL_ONLY = re.compile(r"[^가-힣]+", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)
_SLASH_SPLIT_RE = re.compile(r"\s*/\s*", re.UNICODE)
_HAS_DIGIT_RE = re.compile(r"\d", re.UNICODE)
_HAS_WON_RE = re.compile(r"(원|₩)", re.UNICODE)


def _norm_space(s: str) -> str:
    s = (s or "").strip()
    return _WS_RE.sub(" ", s)


def normalize_menu_korean_only(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    s = _KEEP_HANGUL_ONLY.sub("", s)
    return s.strip()


def _safe_poly(poly: Any) -> List[List[float]]:
    if not isinstance(poly, list) or len(poly) < 4:
        return []
    out = []
    for p in poly:
        if not isinstance(p, (list, tuple)) or len(p) < 2:
            return []
        try:
            out.append([float(p[0]), float(p[1])])
        except Exception:
            return []
    return out


def _poly_bbox(poly: List[List[float]]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _poly_center(poly: List[List[float]]) -> Tuple[float, float]:
    x1, y1, x2, y2 = _poly_bbox(poly)
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def _poly_height(poly: List[List[float]]) -> float:
    _, y1, _, y2 = _poly_bbox(poly)
    return max(1.0, float(y2 - y1))


def _union_poly_bbox(poly_a: List[List[float]], poly_b: List[List[float]]) -> List[List[float]]:
    xs = [p[0] for p in poly_a] + [p[0] for p in poly_b]
    ys = [p[1] for p in poly_a] + [p[1] for p in poly_b]
    x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


def _is_price_like(text: str) -> bool:
    t = _norm_space(text)
    if not t:
        return False
    if _HAS_DIGIT_RE.search(t):
        return True
    if _HAS_WON_RE.search(t):
        return True
    return False


def _is_short_hangul_fragment(text: str) -> bool:
    """Pass1 대상: 한글만 남겼을 때 길이 1~2"""
    t = _norm_space(text)
    if not t:
        return False
    if _is_price_like(t):
        return False
    hn = normalize_menu_korean_only(t)
    return 1 <= len(hn) <= 2


def _is_mergeable_general(text: str) -> bool:
    """Pass2 대상: 한글-only 기준으로 최소 1글자 이상(가격류 제외)"""
    t = _norm_space(text)
    if not t:
        return False
    if _is_price_like(t):
        return False
    hn = normalize_menu_korean_only(t)
    return len(hn) >= 1


def _merge_two(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": str(a["text"]) + str(b["text"]),
        "poly": _union_poly_bbox(a["poly"], b["poly"]),
        "score": float(min(float(a.get("score", 0.0)), float(b.get("score", 0.0)))),
    }


def _line_cluster(items: List[Dict[str, Any]], line_y_tol: int) -> List[List[Dict[str, Any]]]:
    """y center 기준으로 라인 클러스터링"""
    if not items:
        return []
    items_sorted = sorted(items, key=lambda d: _poly_center(d["poly"])[1])
    lines: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []
    cur_y: float = 0.0

    for it in items_sorted:
        _, cy = _poly_center(it["poly"])
        if not cur:
            cur = [it]
            cur_y = cy
            continue
        if abs(cy - cur_y) <= float(line_y_tol):
            cur.append(it)
            # running average for stability
            cur_y = (cur_y * (len(cur) - 1) + cy) / len(cur)
        else:
            lines.append(cur)
            cur = [it]
            cur_y = cy
    if cur:
        lines.append(cur)
    return lines


def _should_merge_pair(
    left: Dict[str, Any],
    right: Dict[str, Any],
    gap_px: int,
    gap_ratio: float,
    pass_mode: str,
) -> bool:
    """병합 여부 판단: x-gap + price-like 차단 + pass별 텍스트 조건"""
    l_text = str(left.get("text", ""))
    r_text = str(right.get("text", ""))

    # 가격/숫자 토큰이 끼면 병합 금지
    if _is_price_like(l_text) or _is_price_like(r_text):
        return False

    # pass별 토큰 조건
    if pass_mode == "pass1":
        if not (_is_short_hangul_fragment(l_text) and _is_short_hangul_fragment(r_text)):
            return False
    else:
        # pass2: 조금 더 넓게 허용하되, 여전히 한글-only가 있어야 함
        if not (_is_mergeable_general(l_text) and _is_mergeable_general(r_text)):
            return False

    # x-gap 조건
    lx1, ly1, lx2, ly2 = _poly_bbox(left["poly"])
    rx1, ry1, rx2, ry2 = _poly_bbox(right["poly"])
    dx = float(rx1 - lx2)
    if dx < -1.0:
        # 겹치거나 역전된 경우는 병합하지 않음(과병합 방지)
        return False
    if dx > float(gap_px):
        return False

    # 해상도 변화 안정화: gap / avg_height
    lh = _poly_height(left["poly"])
    rh = _poly_height(right["poly"])
    avg_h = (lh + rh) / 2.0
    if avg_h > 0:
        if (dx / avg_h) > float(gap_ratio):
            return False

    return True


def _merge_line_once(
    line_items: List[Dict[str, Any]],
    gap_px: int,
    gap_ratio: float,
    pass_mode: str,
) -> List[Dict[str, Any]]:
    """라인 내부 left-to-right 1회 병합"""
    if not line_items:
        return []
    line = sorted(line_items, key=lambda d: _poly_center(d["poly"])[0])
    out: List[Dict[str, Any]] = []
    i = 0
    while i < len(line):
        cur = line[i]
        j = i + 1
        while j < len(line):
            nxt = line[j]

            # 다음 토큰이 가격/숫자면, 여기서 병합을 멈추는 것이 안정적(컬럼 넘어감 방지)
            if _is_price_like(str(nxt.get("text", ""))):
                break

            if _should_merge_pair(cur, nxt, gap_px=gap_px, gap_ratio=gap_ratio, pass_mode=pass_mode):
                cur = _merge_two(cur, nxt)
                j += 1
                continue
            break

        out.append(cur)
        i = j
    return out


def merge_det_items_stable(
    items_raw: List[Dict[str, Any]],
    line_y_tol: int,
    merge_gap_px: int,
    merge_gap_ratio: float,
    pass2_gap_px: int,
    pass2_gap_ratio: float,
    enable_pass2: bool,
) -> List[Dict[str, Any]]:
    """전체 병합: 라인 클러스터 → pass1 → (옵션) pass2"""
    prepared: List[Dict[str, Any]] = []
    for it in items_raw:
        poly = _safe_poly(it.get("poly"))
        if not poly:
            continue
        prepared.append(
            {
                "text": str(it.get("text", "")),
                "poly": poly,
                "score": float(it.get("score", 0.0)),
            }
        )

    lines = _line_cluster(prepared, line_y_tol=int(line_y_tol))

    merged_all: List[Dict[str, Any]] = []
    for ln in lines:
        # pass1: short fragments only (strong & safe)
        p1 = _merge_line_once(ln, gap_px=int(merge_gap_px), gap_ratio=float(merge_gap_ratio), pass_mode="pass1")

        # pass2: optional, for "김치" + "찌개" 같은 케이스를 조건부로 추가 병합
        if enable_pass2:
            p2 = _merge_line_once(p1, gap_px=int(pass2_gap_px), gap_ratio=float(pass2_gap_ratio), pass_mode="pass2")
        else:
            p2 = p1

        merged_all.extend(p2)

    # 안정적 출력 정렬
    merged_all.sort(key=lambda d: (_poly_center(d["poly"])[1], _poly_center(d["poly"])[0]))
    return merged_all


def split_by_slash(raw_text: str) -> List[str]:
    t = _norm_space(raw_text)
    if not t:
        return []
    if "/" not in t:
        return [t]
    parts = [p.strip() for p in _SLASH_SPLIT_RE.split(t)]
    return [p for p in parts if p]


@dataclass
class NormalizeConfig:
    min_len: int = 2
    min_score: float = 0.0


def is_menu_candidate(raw_menu: str, menu_norm: str, score: float, cfg: NormalizeConfig) -> bool:
    if not menu_norm:
        return False
    if len(menu_norm) < cfg.min_len:
        return False
    if score < cfg.min_score:
        return False

    if menu_norm in _NON_MENU_TITLES:
        return False

    t = (raw_menu or "").strip()
    if t.startswith(("※", "*", "•", "-", "·")):
        return False

    for kw in _NON_MENU_HARD_KEYWORDS:
        if kw in menu_norm or kw in t:
            return False

    return True


def run_step_03_normalize(
    ocr_json_path: Path,
    out_json_path: Path,
    cfg: NormalizeConfig,
    line_y_tol: int,
    merge_gap_px: int,
    merge_gap_ratio: float,
    enable_pass2: bool,
    pass2_gap_px: int,
    pass2_gap_ratio: float,
) -> Path:
    with ocr_json_path.open("r", encoding="utf-8") as f:
        ocr = json.load(f)

    items_raw = ocr.get("items", [])

    # 1) Stable merge det-split tokens within each line
    merged_items = merge_det_items_stable(
        items_raw=items_raw,
        line_y_tol=line_y_tol,
        merge_gap_px=merge_gap_px,
        merge_gap_ratio=merge_gap_ratio,
        pass2_gap_px=pass2_gap_px,
        pass2_gap_ratio=pass2_gap_ratio,
        enable_pass2=enable_pass2,
    )

    # 2) Slash-split, then normalize + filter
    items_out: List[Dict[str, Any]] = []
    for it in merged_items:
        raw_text = str(it.get("text", ""))
        poly = it.get("poly")
        score = float(it.get("score", 0.0))

        parts = split_by_slash(raw_text)
        if not parts:
            continue

        for part in parts:
            raw_menu = part
            menu_norm = normalize_menu_korean_only(raw_menu)

            if not is_menu_candidate(raw_menu=raw_menu, menu_norm=menu_norm, score=score, cfg=cfg):
                continue

            items_out.append({"raw_menu": raw_menu, "poly": poly, "menu_norm": menu_norm})

    out = {"items": items_out}
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    with out_json_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return out_json_path


def _find_latest_run_dir(runs_root: Path) -> Path:
    run_dirs = [p for p in runs_root.iterdir() if p.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories under: {runs_root}")
    run_dirs.sort(key=lambda p: p.name)
    return run_dirs[-1]


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Step 03: stable merge det tokens, split by '/', keep raw_menu+poly, produce Hangul-only menu_norm."
    )
    p.add_argument("--runs-root", default="menu_assistant/data/runs", help="Runs root directory")
    p.add_argument("--run-id", default=None, help="Run id (e.g., 20260112_193336). If omitted, use latest.")
    p.add_argument("--out-json", default=None, help="Override output json path")

    p.add_argument("--min-len", type=int, default=2)
    p.add_argument("--min-score", type=float, default=0.0)

    # pass1 (safe)
    p.add_argument("--line-y-tol", type=int, default=20, help="Y tolerance(px) for line clustering.")
    p.add_argument("--merge-gap-px", type=int, default=25, help="Pass1 max X gap(px) to merge short fragments.")
    p.add_argument("--merge-gap-ratio", type=float, default=0.75, help="Pass1 max (gap/avg_height) ratio.")

    # pass2 (conditional)
    p.add_argument("--enable-merge-pass2", action="store_true", help="Enable pass2 conditional merges.")
    p.add_argument("--pass2-gap-px", type=int, default=14, help="Pass2 max X gap(px) (tighter).")
    p.add_argument("--pass2-gap-ratio", type=float, default=0.45, help="Pass2 max (gap/avg_height) ratio (tighter).")

    args = p.parse_args()

    runs_root = Path(args.runs_root)
    run_dir = (runs_root / args.run_id) if args.run_id else _find_latest_run_dir(runs_root)

    in_json = run_dir / "ocr" / "ocr.json"
    if not in_json.exists():
        raise FileNotFoundError(f"Expected input not found: {in_json}")

    out_json = Path(args.out_json) if args.out_json else (run_dir / "normalize" / "normalize.json")

    cfg = NormalizeConfig(min_len=args.min_len, min_score=args.min_score)

    result = run_step_03_normalize(
        ocr_json_path=in_json,
        out_json_path=out_json,
        cfg=cfg,
        line_y_tol=args.line_y_tol,
        merge_gap_px=args.merge_gap_px,
        merge_gap_ratio=args.merge_gap_ratio,
        enable_pass2=bool(args.enable_merge_pass2),
        pass2_gap_px=args.pass2_gap_px,
        pass2_gap_ratio=args.pass2_gap_ratio,
    )

    print("=== step_03_normalize DONE ===")
    print(f"run_dir: {run_dir}")
    print(f"input : {in_json}")
    print(f"output: {result}")
    print(f"config: {cfg}")
    print(
        "merge:",
        f"line_y_tol={args.line_y_tol}",
        f"pass1_gap_px={args.merge_gap_px}",
        f"pass1_gap_ratio={args.merge_gap_ratio}",
        f"pass2={'ON' if args.enable_merge_pass2 else 'OFF'}",
        f"pass2_gap_px={args.pass2_gap_px}",
        f"pass2_gap_ratio={args.pass2_gap_ratio}",
    )
