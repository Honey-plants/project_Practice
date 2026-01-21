from __future__ import annotations

"""inspect_rag_result.py

RAG 결과(rag_match.json)를 사람이 빠르게 점검할 수 있게 요약 출력.

주요 출력:
- status(결정 상태)별로 raw_menu / menu_norm / decided_menu / decision_method 확인
- 필요 시 후보(top-n) 메뉴와 embed/jamo 점수도 함께 출력

실행 예시:
  python inspect_rag_result.py --path rag_match.json
  python menu_assistant/worker/worker_app/utils/inspect_rag_result.py --run-id 20260121_095341
  python inspect_rag_result.py --run-id 20260120_130810 --show-cands --top-n 5

주의:
- 이 스크립트는 "출력(뷰)" 전용입니다. rag_match.json 구조는 수정하지 않습니다.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ----------------------
# Small helpers
# ----------------------

def _load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _clip(s: str, max_len: int = 60) -> str:
    s = _norm(s)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


def _fmt(v: Any) -> str:
    if v is None:
        return "-"
    try:
        return f"{float(v):.3f}"
    except Exception:
        return str(v)


def _resolve_rag_path(run_id: Optional[str], path: Optional[str]) -> Path:
    here = Path(__file__).resolve().parent

    # 1) explicit --path
    if path:
        return Path(path)

    # 2) same folder default
    default_rag_path = here / "rag_match.json"
    if default_rag_path.exists():
        return default_rag_path

    # 3) runs fallback (project legacy)
    # NOTE: 기존 사용자 환경을 고려해 Windows 경로를 유지
    #       (사용자가 다른 환경이면 --path를 주는 것이 안전)
    if run_id:
        base_runs_dir = Path(r"C:\Users\201\Desktop\PGHfolder\haenet\AI\menu_assistant\data\runs")
        cand = base_runs_dir / run_id / "rag_match" / "rag_match.json"
        return cand

    return default_rag_path


def _extract_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = payload.get("items")
    if isinstance(items, list):
        return items
    items = payload.get("results")
    if isinstance(items, list):
        return items
    return []


def _get_fields(item: Dict[str, Any]) -> Tuple[str, str, Optional[str], str, str]:
    """Return (raw_menu, menu_norm, decided_menu, decision_method, status)."""
    raw_menu = _norm(item.get("raw_menu") or item.get("text") or item.get("query"))
    menu_norm = _norm(item.get("menu_norm") or item.get("menu_name_norm") or item.get("menu_name"))

    rag = item.get("rag_match") or {}
    status = _norm(rag.get("status") or item.get("status") or "UNKNOWN")

    decided = rag.get("decided_menu")
    decided_menu = _norm(decided) if decided is not None else None

    decision_method = _norm(rag.get("decision_method") or rag.get("method") or "")

    return raw_menu, menu_norm, decided_menu, decision_method, status


def _print_candidates(rag: Dict[str, Any], top_n: int) -> None:
    cands = rag.get("candidates") or []
    if not isinstance(cands, list) or not cands:
        print("    - candidates: (none)")
        return

    n = max(0, min(int(top_n), len(cands)))
    for i, c in enumerate(cands[:n], start=1):
        if not isinstance(c, dict):
            continue
        menu = _clip(_norm(c.get("menu") or c.get("menu_ko") or c.get("menu_name")), 50) or "UNKNOWN"
        embed = c.get("embed_score")
        jamo = c.get("jamo_score")
        print(f"    {i}) {menu} | embed={_fmt(embed)} jamo={_fmt(jamo)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect Step04 rag_match.json by status")
    ap.add_argument("--run-id", default=None, help="runs/<run-id>/rag_match/rag_match.json fallback용")
    ap.add_argument("--path", default=None, help="rag_match.json 경로 (우선순위 1)")
    ap.add_argument("--top-n", type=int, default=3, help="후보 출력 개수 (show-cands 시)")
    ap.add_argument("--show-cands", action="store_true", help="각 항목의 후보(candidates)까지 출력")
    ap.add_argument("--max-per-status", type=int, default=0, help="status별 출력 최대 개수(0이면 전체)")

    args = ap.parse_args()

    rag_path = _resolve_rag_path(run_id=args.run_id, path=args.path)
    payload = _load_json(rag_path)

    stats = payload.get("stats") or {}
    items = _extract_items(payload)

    # status별 분류
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        _, _, _, _, status = _get_fields(it)
        buckets.setdefault(status or "UNKNOWN", []).append(it)

    # 출력 순서(대표 status) + 나머지
    preferred_order = [
        "EXACT",
        "CONFIRMED_EMBED",
        "AMBIGUOUS_EMBED",
        "CONFIRMED_JAMO",
        "AMBIGUOUS_JAMO",
        "NOT_FOUND_EMPTY_QUERY",
        "NOT_FOUND_NO_CANDIDATES",
        "NOT_FOUND_BELOW_THRESHOLD",
        "UNKNOWN",
    ]
    rest = sorted([k for k in buckets.keys() if k not in preferred_order])
    status_order = [k for k in preferred_order if k in buckets] + rest

    # ========================
    # SUMMARY
    # ========================
    print("=" * 80)
    print("RAG MATCH SUMMARY (status buckets)")
    print("=" * 80)
    if args.run_id:
        print(f"run_id   : {args.run_id}")
    print(f"rag_path : {rag_path}")
    if stats:
        print(f"stats    : {stats}")

    # bucket counts
    cnt_line = " | ".join([f"{k}={len(buckets[k])}" for k in status_order])
    print(f"counts   : {cnt_line}")
    print("=" * 80)

    # ========================
    # DETAILS
    # ========================
    for st in status_order:
        print(f"\n[{st}]")
        arr = buckets.get(st) or []
        if not arr:
            print("- (none)")
            continue

        limit = int(args.max_per_status)
        if limit > 0:
            arr = arr[:limit]

        for it in arr:
            raw_menu, menu_norm, decided_menu, decision_method, _ = _get_fields(it)
            rag = it.get("rag_match") or {}

            raw_s = _clip(raw_menu, 40) or "-"
            norm_s = _clip(menu_norm, 40) or "-"
            decided_s = _clip(decided_menu or "", 40) if decided_menu else "-"
            method_s = decision_method or "-"

            # 한 줄 요약
            print(f"- menu_norm={norm_s} | raw_menu={raw_s} | decided_menu={decided_s} | method={method_s}")

            # 부가 신호(있으면)
            signals = rag.get("signals") or {}
            if isinstance(signals, dict) and signals:
                top1_menu = signals.get("top1_menu")
                top1_embed = signals.get("top1_embed")
                best_jamo_menu = signals.get("best_jamo_menu")
                best_jamo_score = signals.get("best_jamo_score")

                # 신호는 너무 길면 지저분하므로 존재할 때만 최소 출력
                parts: List[str] = []
                if top1_menu is not None:
                    parts.append(f"top1={_clip(_norm(top1_menu), 30)}")
                if top1_embed is not None:
                    parts.append(f"embed={_fmt(top1_embed)}")
                if best_jamo_menu is not None:
                    parts.append(f"best_jamo={_clip(_norm(best_jamo_menu), 30)}")
                if best_jamo_score is not None:
                    parts.append(f"jamo={_fmt(best_jamo_score)}")
                if parts:
                    print("  signals: " + ", ".join(parts))

            if args.show_cands:
                _print_candidates(rag, top_n=args.top_n)


if __name__ == "__main__":
    main()
