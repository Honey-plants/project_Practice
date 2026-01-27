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
    # fixed hard blocks (policy / notice)
    "원산지", "국내산", "수입산",
    "포장", "배달", "환불", "결제",
    "문의", "전화",
    "알레르기", "알러지", "주의",

    # menu-board notices / operational words
    "공지", "안내", "참고", "유의", "필독",
    "테이블", "카운터", "셀프", "리필", "무료", "서비스",
    "주문", "주문서", "계산", "계산대", "결제", "포장가능", "배달가능",
    "영업", "시간", "휴무", "브레이크", "라스트오더",

    # choice / option phrases (typical set explanation)
    "선택", "중선택", "메뉴북", "대신", "가능", "변경", "추가요금", "개당",
]

# Titles / section headers (should be removed)
_NON_MENU_TITLES = {
    "안주", "사이드", "추가", "추가메뉴", "사리", "음료", "음료수", "주류", "메뉴",
    "세트", "세트메뉴", "코스", "런치", "디너", "세트구성", "구성",
    "옵션", "선택", "추천", "베스트",
}

_KEEP_HANGUL_ONLY = re.compile(r"[^가-힣]+", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)
_SLASH_SPLIT_RE = re.compile(r"\s*/\s*", re.UNICODE)
_HAS_DIGIT_RE = re.compile(r"\d", re.UNICODE)
_HAS_WON_RE = re.compile(r"(원|₩)", re.UNICODE)

# Extra non-menu detection (set/notice/instruction lines)
# - We keep final output as menu_norm, but we filter early to reduce RAG noise.
# - This is intentionally conservative: it targets set 구성/선택/안내문구.
_NON_MENU_PATTERNS = [
    re.compile(r"\bSET\b", re.IGNORECASE),
    re.compile(r"\bMENU\b", re.IGNORECASE),
    re.compile(r"\bfrom\b", re.IGNORECASE),
    re.compile(r"\bor\b", re.IGNORECASE),
    re.compile(r"\+\s*\d+\s*(천원|만원|원)", re.UNICODE),
    re.compile(r"\d+\s*인\s*세트", re.UNICODE),
    re.compile(r"\b\d+\s*잔\b", re.UNICODE),
    re.compile(r"(중\s*선택|중선택|메뉴\s*선택|대신|가능|변경|추가요금|개당)", re.UNICODE),
]

# If a line is mostly a 'selection instruction', treat as non-menu.
_SELECTION_HINTS = [
    "선택", "중선택", "대신", "가능", "변경", "메뉴북", "메뉴", "옵션",
]

# Components often appearing in set descriptions. If the string contains these WITH selection hints,
# it is very likely not a standalone menu name.
_SET_COMPONENT_WORDS = {
    "스프", "후식", "드링크", "와인", "샐러드", "샐러드", "파스타", "리조토", "피자",
}


def _contains_any(s: str, words) -> bool:
    for w in words:
        if w and w in s:
            return True
    return False


def _looks_like_set_or_notice(raw_text: str, menu_norm: str) -> bool:
    """Return True if the token likely represents set/notice/instruction rather than a menu item."""
    t = _norm_space(raw_text)
    if not t:
        return True

    # headers already handled by _NON_MENU_TITLES, but catch common English headings
    for pat in _NON_MENU_PATTERNS:
        if pat.search(t):
            # If it contains actual Hangul menu and no selection hints, don't over-filter.
            # Example: '찹스테이크' should pass, 'SET MENU', 'from 59,500', '파스타/.. 중 선택1' should not.
            # Here, patterns mostly indicate instruction or set.
            return True

    # Strong selection / instruction signals
    if _contains_any(t, _SELECTION_HINTS):
        return True

    # If raw text includes set component words AND looks like instruction, filter.
    if _contains_any(menu_norm, _SET_COMPONENT_WORDS) and ("선택" in t or "중" in t or "or" in t.lower()):
        return True

    # Standalone set word or variants like '세트(2인)'
    if "세트" in t or "세트" in menu_norm:
        return True

    return False


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

def _y_overlap_ratio(a: List[List[float]], b: List[List[float]]) -> float:
    """Two bboxes' vertical overlap ratio over min height. 0.0 ~ 1.0"""
    ax1, ay1, ax2, ay2 = _poly_bbox(a)
    bx1, by1, bx2, by2 = _poly_bbox(b)
    inter = max(0.0, min(ay2, by2) - max(ay1, by1))
    ha = max(1.0, ay2 - ay1)
    hb = max(1.0, by2 - by1)
    denom = min(ha, hb)
    return float(inter / denom) if denom > 0 else 0.0


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

    # (가드1) 좌->우 순서가 깨진 '역전'은 병합 금지 (과병합 방지)
    # right가 left보다 확실히 왼쪽에 있으면 reversed로 본다.

    if float(rx2) <= float(lx1):

        return False

    # (가드2) 세로로 충분히 겹치지 않으면 병합 금지 (라인 섞임 방지)
    # line_cluster가 y-center 기반이므로, 여기서 한 번 더 안정화한다.

    if _y_overlap_ratio(left["poly"], right["poly"]) < 0.60:

        return False

    # (핵심) dx가 음수(겹침)인 경우를 제한적으로 허용
    # - 너무 많이 겹치면(큰 음수) 다른 컬럼/라인 토큰을 빨아들일 위험이 있으므로 제한
    lh = _poly_height(left["poly"])
    rh = _poly_height(right["poly"])
    avg_h = (lh + rh) / 2.0

    # overlap 허용치: min(절대 px, 상대 비율)
    overlap_tol_px = 6.0
    overlap_tol_ratio = 0.20  # avg_h의 20%까지 음수 dx 허용
    overlap_tol = min(overlap_tol_px, float(avg_h) * overlap_tol_ratio)

    if dx < 0.0:

        if abs(dx) > overlap_tol:

            return False
      # 겹침은 허용하되, gap 제한은 '양수 dx'에만 적용
    else:

        if dx > float(gap_px):

            return False
      # 해상도 변화 안정화: gap / avg_height (양수 dx일 때만 의미가 큼)

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
    # center-x는 겹침 케이스에서 순서가 흔들릴 수 있으므로 bbox x1 기준으로 안정화
    line = sorted(line_items, key=lambda d: _poly_bbox(d["poly"])[0])
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
    # ------------------------------------------------------------------
    # Special case: "옵션/재료/토핑 나열 + 공백 + 메인메뉴"
    # e.g., "새우/전복/문어 비프찹스테이크"  -> ["비프찹스테이크"]
    #
    # Rationale:
    # naive split makes "문어 비프찹스테이크" -> normalize -> "문어비프찹스테이크"
    # which is incorrect menu query for RAG.
    # ------------------------------------------------------------------

    if " " in t:
        left, right = t.rsplit(" ", 1)
  # left must contain slashes; right should look like a menu token after hangul-only normalize

        if "/" in left:
            right_norm = normalize_menu_korean_only(right)
            left_norm = normalize_menu_korean_only(left.replace("/", ""))
    # conservative guards:
    # - right should contain meaningful Hangul
    # - left should not be empty (it is option list)

            if right_norm and left_norm:
                return [right]

    # Fallback: standard slash split
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
    # set / notice / instruction filtering (reduces RAG noise)
    if _looks_like_set_or_notice(raw_text=t, menu_norm=menu_norm):
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
