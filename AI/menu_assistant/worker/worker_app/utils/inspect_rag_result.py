from __future__ import annotations

"""inspect_rag_result.py

RAG 결과(rag_match.json)를 사람이 빠르게 점검할 수 있게 요약 출력.

주요 출력:
- match_status(결정 상태)별로 raw_menu / menu_norm / menu_final / match_decision_method 확인
- confirmed 블록(있으면) 재료/알러지 태그 요약
- 필요 시 후보(top-n) 메뉴와 embed/jamo 점수도 함께 출력

실행 예시:
  python inspect_rag_result.py --path rag_match.json
  python menu_assistant/worker/worker_app/utils/inspect_rag_result.py --run-id 20260123_131220
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
    """Return (raw_menu, menu_norm, menu_final, decision_method, status).

    Supports both:
    - New schema: match_status / match_decision_method / menu_final / confirmed / match
    - Legacy schema: rag_match.status / rag_match.decided_menu / rag_match.decision_method
    """
    raw_menu = _norm(item.get("raw_menu") or item.get("text") or item.get("query"))
    menu_norm = _norm(item.get("menu_norm") or item.get("menu_name_norm") or item.get("menu_name"))

    # New schema first
    status = _norm(item.get("match_status") or item.get("status") or "UNKNOWN")
    decision_method = _norm(item.get("match_decision_method") or item.get("decision_method") or "")

    menu_final_val = item.get("menu_final")
    menu_final = _norm(menu_final_val) if menu_final_val is not None else None

    # Legacy fallback
    if status == "UNKNOWN" or (not decision_method and "rag_match" in item):
        rag = item.get("rag_match") or {}
        status = _norm(rag.get("status") or status or "UNKNOWN")
        menu_final_val = rag.get("decided_menu")
        menu_final = _norm(menu_final_val) if menu_final_val is not None else menu_final
        decision_method = _norm(rag.get("decision_method") or rag.get("method") or decision_method or "")

    return raw_menu, menu_norm, menu_final, decision_method, status


def _print_candidates(match_obj: Dict[str, Any], top_n: int) -> None:
    cands = match_obj.get("candidates") or []
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
        final = c.get("final_score")
        bv = _clip(_norm(c.get("best_variant")), 18) if c.get("best_variant") else "-"
        print(f"    {i}) {menu} | final={_fmt(final)} embed={_fmt(embed)} jamo={_fmt(jamo)} best_v={bv}")


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
            raw_menu, menu_norm, menu_final, decision_method, _ = _get_fields(it)
            match_obj = it.get("match") or {}  # new schema
            rag = it.get("rag_match") or {}  # legacy fallback

            raw_s = _clip(raw_menu, 40) or "-"
            norm_s = _clip(menu_norm, 40) or "-"
            decided_s = _clip(menu_final or "", 40) if menu_final else "-"
            method_s = decision_method or "-"

            # 한 줄 요약
            print(f"- menu_norm={norm_s} | raw_menu={raw_s} | menu_final={decided_s} | method={method_s}")

            # confirmed summary (EXACT only)
            conf = it.get('confirmed')
            if isinstance(conf, dict) and conf:
                c_menu = _clip(_norm(conf.get('menu')), 30) or '-'
                alg = conf.get('alg_tags')
                alg_s = _clip(', '.join(map(str, alg)) if isinstance(alg, list) else _norm(alg), 60) if alg else '-'
                print(f"  confirmed: menu={c_menu} | alg_tags={alg_s}")

            # 부가 신호(있으면)
            # Minimal signals: show best + thresholds if present
            thresholds = match_obj.get("thresholds") if isinstance(match_obj, dict) else None
            best = match_obj.get("best") if isinstance(match_obj, dict) else None
            parts: List[str] = []
            if isinstance(best, dict):
                if best.get("menu"):
                    parts.append(f"best={_clip(_norm(best.get('menu')), 30)}")
                if best.get("final_score") is not None:
                    parts.append(f"final={_fmt(best.get('final_score'))}")
                if best.get("best_variant"):
                    parts.append(f"best_v={_clip(_norm(best.get('best_variant')), 20)}")
            if isinstance(thresholds, dict) and thresholds:
                # show only key thresholds
                jamo_min = thresholds.get("jamo_min")
                final_close = thresholds.get("final_close")
                if jamo_min is not None:
                    parts.append(f"jamo_min={_fmt(jamo_min)}")
                if final_close is not None:
                    parts.append(f"final_close={_fmt(final_close)}")
            if parts:
                print("  match: " + ", ".join(parts))

            if args.show_cands:
                _print_candidates(match_obj if isinstance(match_obj, dict) else rag, top_n=args.top_n)


if __name__ == "__main__":
    main()
