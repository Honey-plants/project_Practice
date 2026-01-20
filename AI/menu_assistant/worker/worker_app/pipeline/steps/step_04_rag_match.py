# menu_assistant/worker/worker_app/pipeline/steps/step_04_rag_match.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from menu_assistant.worker.worker_app.rag.retrieval import match_menu_norm


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _resolve_run_dir(data_dir: Path, run_id: str) -> Path:
    return data_dir / "runs" / run_id


def run_step_04_rag_match(
    run_dir: Path,
    top_k: int = 5,
    embed_ambiguous: float = 0.90,
    jamo_threshold: float = 0.85,
    score_threshold: float = 0.55,
    save_top_n: int = 2,
    include_debug: bool = False,
) -> Path:
    normalize_path = run_dir / "normalize" / "normalize.json"
    if not normalize_path.exists():
        alt = run_dir / "normalize" / "normalized.json"
        if alt.exists():
            normalize_path = alt
        else:
            raise FileNotFoundError(f"normalize output not found: {normalize_path}")

    normalized = _read_json(normalize_path)

    # Step03 표준 스키마: {"items":[{raw_menu, poly, menu_norm}]}
    items = None
    if isinstance(normalized, dict) and isinstance(normalized.get("items"), list):
        items = normalized["items"]
    elif isinstance(normalized, dict):
        # 과거 스키마 호환(있을 수 있으니)
        for k in ("items_merged", "lines", "results"):
            if isinstance(normalized.get(k), list):
                items = normalized[k]
                break
    elif isinstance(normalized, list):
        items = normalized

    if not isinstance(items, list):
        raise ValueError(f"normalize json schema not supported: {type(normalized)}")

    out_items: List[Dict[str, Any]] = []
    stats = {"EXACT": 0, "AMBIGUOUS": 0, "NOT_FOUND": 0, "TOTAL": 0}

    for it in items:
        if not isinstance(it, dict):
            continue

        menu_norm = str(it.get("menu_norm") or "").strip()

        rag = match_menu_norm(
            menu_norm=menu_norm,
            top_k=int(top_k),
            embed_ambiguous=float(embed_ambiguous),
            jamo_threshold=float(jamo_threshold),
            score_threshold=float(score_threshold),
            save_top_n=int(save_top_n),
            include_debug=include_debug,
        )

        merged = dict(it)
        merged["rag_match"] = rag

        # 최종 결정된 메뉴가 있으면, 그 메뉴명을 "menu_final"로 별도 저장(사용 편의)
        merged["menu_final"] = rag.get("decided_menu")

        # 알러지/재료는 best_match에서 바로 끌어올 수도 있음
        bm = rag.get("best_match") or {}
        merged["ingredients_ko"] = bm.get("ingredients_ko") if isinstance(bm, dict) else None
        merged["alg_tags"] = bm.get("alg_tags") if isinstance(bm, dict) else None

        out_items.append(merged)

        stats["TOTAL"] += 1
        st = rag.get("status") or "NOT_FOUND"
        if st in stats:
            stats[st] += 1
        else:
            stats["NOT_FOUND"] += 1

    out_path = run_dir / "rag_match" / "rag_match.json"
    payload = {
        "run_dir": str(run_dir),
        "input_normalize": str(normalize_path),
        "config": {
            "top_k": int(top_k),
            "embed_ambiguous": float(embed_ambiguous),
            "jamo_threshold": float(jamo_threshold),
            "score_threshold": float(score_threshold),
            "save_top_n": int(save_top_n),
        },
        "stats": stats,
        "items": out_items,
    }
    _write_json(out_path, payload)
    return out_path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Step04 RAG match (menu_norm-only, menu-only compare, exact/amb/jamo)")
    p.add_argument("--run_id", type=str, required=False)
    p.add_argument("--data_dir", type=str, default=None)
    p.add_argument("--run_dir", type=str, default=None)

    p.add_argument("--top_k", type=int, default=5)
    p.add_argument("--embed_ambiguous", type=float, default=0.90)
    p.add_argument("--jamo_threshold", type=float, default=0.85)
    p.add_argument("--score_threshold", type=float, default=0.55)
    p.add_argument("--save_top_n", type=int, default=2)

    # orchestrator 호환용(받기만 하고 사용하지 않음)
    p.add_argument("--rerank_top_k", type=int, default=0)
    p.add_argument("--use_rerank", action="store_true")
    p.add_argument("--no_rerank", action="store_true")

    p.add_argument("--include_debug", action="store_true")
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
        embed_ambiguous=args.embed_ambiguous,
        jamo_threshold=args.jamo_threshold,
        score_threshold=args.score_threshold,
        save_top_n=args.save_top_n,
        include_debug=args.include_debug,
    )
    print(f"[Step04] wrote: {out_path}")


if __name__ == "__main__":
    main()
