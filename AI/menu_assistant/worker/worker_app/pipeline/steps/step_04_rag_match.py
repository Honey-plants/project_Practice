from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from menu_assistant.worker.worker_app.rag.retrieval import match_menu_norm


def _canon_status(status_raw: str) -> str:
    """Normalize detailed/raw statuses into canonical statuses for downstream.

    Canonical: exact | close | ambiguous | not_found
    Raw examples kept for analytics: EXACT, CLOSE, NOT_FOUND_BELOW_THRESHOLD, ...
    """
    s = (status_raw or "").strip().lower()
    if "exact" in s:
        return "exact"
    if "close" in s:
        return "close"
    if "ambiguous" in s:
        return "ambiguous"
    if "not_found" in s:
        return "not_found"
    return "not_found"


# ============================================================
# Exact precheck (STRING EXACT) before embedding search
# - Optional and backward compatible
# - Enabled when --menu_index_json is provided OR env var
#   MENU_ASSISTANT_MENU_INDEX_JSON is set.
# - This prevents cases where an exact menu exists in the index
#   but is not retrieved by embedding top_k candidates.
# ============================================================
menu_index_json = "AI/menu_assistant/data/datasets/raw/menu_seed_with_alg_tags_variants_v3.json"


def _load_menu_index_for_exact(path_str: Optional[str]) -> Optional[Dict[str, Dict[str, Any]]]:
    """Load a menu index json (list of entries) and build variant->record map."""
    p = (path_str or os.environ.get("MENU_ASSISTANT_MENU_INDEX_JSON") or "").strip()
    if not p:
        return None
    path = Path(p).expanduser()
    if not path.exists():
        print(f"[WARN] menu_index_json not found: {path}")
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] failed to read menu_index_json: {path} ({type(e).__name__}: {e})")
        return None

    entries: List[Dict[str, Any]] = []
    if isinstance(obj, dict) and isinstance(obj.get("items"), list):
        entries = obj["items"]
    elif isinstance(obj, list):
        entries = obj
    else:
        print(f"[WARN] menu_index_json schema unsupported: {type(obj)}")
        return None

    vmap: Dict[str, Dict[str, Any]] = {}
    for it in entries:
        if not isinstance(it, dict):
            continue
        menu = str(it.get("menu") or "").strip()
        if menu:
            vmap.setdefault(menu, it)
        variants = it.get("variants")
        if isinstance(variants, list):
            for v in variants:
                if isinstance(v, str):
                    vv = v.strip()
                    if vv:
                        vmap.setdefault(vv, it)
    if not vmap:
        print(f"[WARN] menu_index_json loaded but empty: {path}")
        return None
    print(f"[INFO] exact-precheck index loaded: {path} (variants={len(vmap)})")
    return vmap


def _exact_precheck(menu_norm: str, vmap: Optional[Dict[str, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    if not vmap:
        return None
    q = (menu_norm or "").strip()
    if not q:
        return None
    hit = vmap.get(q)
    if not isinstance(hit, dict):
        return None

    best_match = {
        "id": hit.get("id"),
        "menu": hit.get("menu"),
        "best_variant": q,
        "embed_score": 1.0,
        "jamo_score": 1.0,
        "final_score": 1.0,
        "ingredients_ko": hit.get("ingredients_ko") or [],
        "alg_tags": hit.get("alg_tags") or [],
    }
    return {
        "status": "EXACT",
        "decision_method": "STRING_EXACT_PRECHECK",
        "used_query": q,
        "best_match": best_match,
        "candidates": [],
        "signals": {"thresholds": {}},
        "debug": None,
        "decided_menu": hit.get("menu"),
    }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _resolve_run_dir(data_dir: Path, run_id: str) -> Path:
    return data_dir / "runs" / run_id


def _extract_items(normalized: Any) -> List[Dict[str, Any]]:
    if isinstance(normalized, dict):
        if isinstance(normalized.get("items"), list):
            return normalized["items"]
        for k in ("items_merged", "lines", "results"):
            if isinstance(normalized.get(k), list):
                return normalized[k]
        raise ValueError(f"normalize json schema not supported. keys={list(normalized.keys())}")
    if isinstance(normalized, list):
        return normalized
    raise ValueError(f"normalize json must be dict or list, got {type(normalized)}")


def run_step_04_rag_match(
    run_dir: Path,
    top_k: int = 5,
    save_top_n: int = 2,
    embed_ambiguous: float = 0.90,
    embed_confirmed: float = 0.95,
    jamo_threshold: float = 0.85,
    jamo_confirmed: float = 0.95,
    score_threshold: float = 0.55,
    include_debug: bool = False,
    menu_index_json: Optional[str] = None,
) -> Path:
    normalize_path = run_dir / "normalize" / "normalize.json"
    if not normalize_path.exists():
        alt = run_dir / "normalize" / "normalized.json"
        if alt.exists():
            normalize_path = alt
        else:
            raise FileNotFoundError(f"normalize output not found: {normalize_path}")

    normalized = _read_json(normalize_path)
    items = _extract_items(normalized)

    exact_vmap = _load_menu_index_for_exact(menu_index_json)

    out_items: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {
        "EXACT": 0,
        "CONFIRMED_EMBED": 0,
        "AMBIGUOUS_EMBED": 0,
        "CONFIRMED_JAMO": 0,
        "AMBIGUOUS_JAMO": 0,
        "NOT_FOUND_EMPTY_QUERY": 0,
        "NOT_FOUND_NO_CANDIDATES": 0,
        "NOT_FOUND_BELOW_THRESHOLD": 0,
        "TOTAL": 0,
    }

    for it in items:
        if not isinstance(it, dict):
            continue

        menu_norm = str(it.get("menu_norm") or "").strip()
        raw_menu = str(
            it.get("raw_menu")
            or it.get("menu_raw")
            or it.get("text")
            or it.get("menu")
            or it.get("query")
            or ""
        ).strip()

        exact_rag = _exact_precheck(menu_norm, exact_vmap)
        if exact_rag is not None:
            rag = exact_rag
        else:
            rag = match_menu_norm(
                menu_norm=menu_norm,
                raw_menu=raw_menu,
                top_k=int(top_k),
                save_top_n=int(save_top_n),
                embed_ambiguous=float(embed_ambiguous),
                jamo_threshold=float(jamo_threshold),
                score_threshold=float(score_threshold),
                include_debug=include_debug,
            )

        # ------------------------------
        # Canonicalize status for downstream rules/UI.
        # Keep raw for debug/analytics.
        # This supports both retrieval.py (status/status_raw) and legacy outputs.
        # ------------------------------
        raw_status = rag.get("status_raw") or rag.get("status")
        canon_status = _canon_status(str(raw_status or ""))
        rag["status_raw"] = raw_status
        rag["status"] = canon_status

        merged = dict(it)

        merged["raw_menu"] = raw_menu or merged.get("raw_menu")
        merged["menu_norm"] = menu_norm or merged.get("menu_norm")
        merged["menu_final"] = rag.get("decided_menu")
        merged["match_status"] = canon_status
        merged["match_status_raw"] = raw_status
        merged["match_decision_method"] = rag.get("decision_method")

        bm = rag.get("best_match") or {}
        signals = rag.get("signals") or {}
        merged["match"] = {
            "used_query": rag.get("used_query"),
            "best": {
                "id": bm.get("id") if isinstance(bm, dict) else None,
                "menu": bm.get("menu") if isinstance(bm, dict) else None,
                "best_variant": bm.get("best_variant") if isinstance(bm, dict) else None,
                "embed_score": bm.get("embed_score") if isinstance(bm, dict) else None,
                "jamo_score": bm.get("jamo_score") if isinstance(bm, dict) else None,
                "final_score": bm.get("final_score") if isinstance(bm, dict) else None,
            },
            "candidates": rag.get("candidates") or [],
            "thresholds": (signals.get("thresholds") or {}) if isinstance(signals, dict) else {},
            "debug": rag.get("debug") if include_debug else None,
        }

        # Confirmed payload: ONLY when EXACT
        if canon_status == "exact" and isinstance(bm, dict):
            merged["confirmed"] = {
                "menu_id": bm.get("id"),
                "menu": bm.get("menu"),
                "ingredients_ko": bm.get("ingredients_ko"),
                "alg_tags": bm.get("alg_tags"),
            }
        else:
            merged["confirmed"] = None

        merged["rag_match"] = rag

        out_items.append(merged)

        stats["TOTAL"] += 1
        # stats keeps raw statuses (backward-compat)
        st_raw = str(raw_status or "")
        stats[st_raw] = stats.get(st_raw, 0) + 1

    out_path = run_dir / "rag_match" / "rag_match.json"
    payload = {
        "run_dir": str(run_dir),
        "input_normalize": str(normalize_path),
        "config": {
            "top_k": int(top_k),
            "save_top_n": int(save_top_n),
            "embed_ambiguous": float(embed_ambiguous),
            "jamo_threshold": float(jamo_threshold),
            "reserved": {
                "embed_confirmed": float(embed_confirmed),
                "jamo_confirmed": float(jamo_confirmed),
            },
            "score_threshold": float(score_threshold),
            "exact_precheck": {
                "enabled": bool(exact_vmap is not None),
                "menu_index_json": (menu_index_json or os.environ.get("MENU_ASSISTANT_MENU_INDEX_JSON") or None),
            },
        },
        "stats": stats,
        "items": out_items,
    }
    _write_json(out_path, payload)
    return out_path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Step04 RAG match (menu_norm-only query, menu-only compare, granular statuses)"
    )
    p.add_argument("--run_id", type=str, required=False)
    p.add_argument("--data_dir", type=str, default=None)
    p.add_argument("--run_dir", type=str, default=None)

    p.add_argument("--top_k", type=int, default=5)
    p.add_argument("--save_top_n", type=int, default=2)

    p.add_argument("--embed_ambiguous", type=float, default=0.90)
    p.add_argument("--embed_confirmed", type=float, default=0.95)
    p.add_argument("--jamo_threshold", type=float, default=0.85)
    p.add_argument("--jamo_confirmed", type=float, default=0.95)
    p.add_argument("--score_threshold", type=float, default=0.55)

    p.add_argument("--rerank_top_k", type=int, default=0)
    p.add_argument("--use_rerank", action="store_true")
    p.add_argument("--no_rerank", action="store_true")

    p.add_argument("--include_debug", action="store_true")
    p.add_argument(
        "--menu_index_json",
        type=str,
        default=menu_index_json,
        help="Optional menu index json for STRING EXACT precheck. If omitted, uses env MENU_ASSISTANT_MENU_INDEX_JSON.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    repo_root = Path(__file__).resolve().parents[4]  # menu_assistant/
    default_data_dir = repo_root / "data"
    data_dir = Path(args.data_dir) if args.data_dir else default_data_dir

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        if not args.run_id:
            raise ValueError("Either --run_dir or --run_id must be provided.")
        run_dir = _resolve_run_dir(data_dir, args.run_id)

    out_path = run_step_04_rag_match(
        run_dir=run_dir,
        top_k=args.top_k,
        save_top_n=args.save_top_n,
        embed_ambiguous=args.embed_ambiguous,
        embed_confirmed=args.embed_confirmed,
        jamo_threshold=args.jamo_threshold,
        jamo_confirmed=args.jamo_confirmed,
        score_threshold=args.score_threshold,
        include_debug=args.include_debug,
        menu_index_json=args.menu_index_json,
    )
    print(f"[Step04] wrote: {out_path}")


if __name__ == "__main__":
    main()
