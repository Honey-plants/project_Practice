# C:\Users\201\Desktop\PGHfolder\haenet\AI\menu_assistant\worker\worker_app\pipeline\steps\step_05_risk_score.py
"""
Step 05 (Runner):
- Input : <data_dir>/runs/<run_id>/rag_match/rag_match.json
- Output:
    <run_dir>/llm/llm_input.json
    <run_dir>/llm/llm_input_meta.json
    <run_dir>/llm/llm_prompt.txt              (optional debug)
    <run_dir>/llm/llm_raw.txt                 (optional debug)
    <run_dir>/llm/llm_output.json             (validated JSON)

Flow:
  rag_match.json
    -> llm/services/decision_rules.py   (EXACT/CLOSE only, poly required, item_id assigned)
    -> llm/services/finalizer.py        (payload normalization for LLM)
    -> llm/prompt_builder.py            (build system+user prompt with "final JSON structure")
    -> llm/client.py                    (Gemini 2.5 Flash call)
    -> llm/parsers.py                   (extract JSON + schema validation; retry loop here)
    -> save llm_output.json

LLM Output Required fields per item:
  item_id, menu_name, poly, menu_description_ko, risk_description_ko
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text or "")


def _resolve_run_dir(data_dir: Path, run_id: str) -> Path:
    return data_dir / "runs" / run_id


def _profile_categories_to_minimal(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert "categories-based" profile schema to the minimal schema consumed by Step05/LLM.

    Supports both:
      - category_label_en: allergy/religion/dislike/vegan
      - category_label_ko: 알러지/종교/싫어하는 음식/비건

    Output (minimal):
      {
        "allergy_tags": ["ALG_PEANUT", ...],
        "avoid_foods": ["돼지고기", ...],   # union of blocked_ingredients_ko across relevant categories
        "religion": "islam_halal" | None
      }
    """
    categories = obj.get("categories")
    if not isinstance(categories, list):
        # Not categories schema
        return {}

    # Use sets for stable de-dup
    allergy_tags_set: set[str] = set()
    avoid_foods_set: set[str] = set()
    religion: Any = None

    KO_LABEL_MAP = {
        "알러지": "allergy",
        "알레르기": "allergy",
        "종교": "religion",
        "싫어하는 음식": "dislike",
        "기피": "dislike",
        "비건": "vegan",
        "채식": "vegan",
    }

    def _norm_str(x: Any) -> str:
        if not isinstance(x, str):
            return ""
        return x.strip()

    def _add_values(dst: set[str], values: Any) -> None:
        if not values:
            return
        if isinstance(values, str):
            v = values.strip()
            if v:
                dst.add(v)
            return
        if isinstance(values, list):
            for x in values:
                if isinstance(x, str):
                    v = x.strip()
                    if v:
                        dst.add(v)

    for cat in categories:
        if not isinstance(cat, dict):
            continue

        label_en = _norm_str(cat.get("category_label_en")).lower()
        if not label_en:
            label_ko = _norm_str(cat.get("category_label_ko"))
            label_en = KO_LABEL_MAP.get(label_ko, "")
        items = cat.get("items")
        if not isinstance(items, list):
            continue

        if label_en == "allergy":
            for it in items:
                if not isinstance(it, dict):
                    continue
                # Primary: alg_tags
                _add_values(allergy_tags_set, it.get("alg_tags"))
                # Fallback: item_label_en (when it is an ALG_* tag)
                ile = it.get("item_label_en")
                if isinstance(ile, str) and ile.strip().upper().startswith("ALG_"):
                    allergy_tags_set.add(ile.strip().upper())
                # Some profiles might store blocked_ingredients_ko even for allergies
                _add_values(avoid_foods_set, it.get("blocked_ingredients_ko"))

        elif label_en == "religion":
            # Use the first item as the active religion (MVP)
            if religion is None and items:
                first = items[0]
                if isinstance(first, dict):
                    religion = first.get("item_label_en") or first.get("item_label_ko") or None
                    if isinstance(religion, str):
                        religion = religion.strip() or None
            # For safety, also include blocked ingredients as avoid_foods
            for it in items:
                if not isinstance(it, dict):
                    continue
                _add_values(avoid_foods_set, it.get("blocked_ingredients_ko"))

        elif label_en in ("dislike", "vegan"):
            for it in items:
                if not isinstance(it, dict):
                    continue
                _add_values(avoid_foods_set, it.get("blocked_ingredients_ko"))

        else:
            # Unknown category: ignore
            continue

    return {
        "allergy_tags": sorted(allergy_tags_set),
        "avoid_foods": sorted(avoid_foods_set),
        "religion": religion,
    }

def _load_user_profile(user_profile_json: str) -> Dict[str, Any]:
    # """
    # Step05 consumes a minimal user profile schema:
    #
    #   {
    #     "allergy_tags": [...],   # e.g. ["ALG_PEANUT", "ALG_CRUSTACEANS"]
    #     "avoid_foods": [...],    # ingredient/food tokens in Korean (or consistent tokens)
    #     "religion": "..." | None
    #   }
    #
    # However, your project also uses a richer "categories" schema.
    # This loader supports BOTH shapes:
    #   - If the JSON already has allergy_tags/avoid_foods/religion, it is used as-is (with defaults).
    #   - If the JSON has a "categories" list, it is converted into the minimal schema above.
    # """
    if not user_profile_json:
        return {"allergy_tags": [], "avoid_foods": [], "religion": None}

    p = Path(user_profile_json)
    if not p.exists():
        raise FileNotFoundError(f"user_profile_json not found: {p}")
    obj = _read_json(p)
    if not isinstance(obj, dict):
        raise ValueError("user_profile_json must be a JSON object (dict).")

    # Common wrapper keys (front/back-end payloads often wrap the profile)
    for wrap_key in ("user_profile", "profile", "data"):
        if isinstance(obj.get(wrap_key), dict):
            obj = obj[wrap_key]
            break

    # 1) If it is already minimal schema, keep it.
    if any(k in obj for k in ("allergy_tags", "avoid_foods", "religion")):
        obj.setdefault("allergy_tags", [])
        obj.setdefault("avoid_foods", [])
        obj.setdefault("religion", None)
        return obj

    # 2) Convert categories schema -> minimal schema
    converted = _profile_categories_to_minimal(obj)
    if isinstance(converted, dict) and set(converted.keys()) >= {"allergy_tags", "avoid_foods", "religion"}:
        return converted

    # 3) Fallback: return safe defaults
    return {"allergy_tags": [], "avoid_foods": [], "religion": None}

def _normalize_llm_input_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure LLM input item has:
      - item_id
      - menu_name (exact: menu, close: decided_menu)
      - poly
      - evidence (optional): ingredients_ko, alg_tags, menu_id
    The LLM is instructed to COPY item_id/menu_name/poly exactly.
    """
    out: List[Dict[str, Any]] = []
    for it in items:
        status = str(it.get("status", "")).lower().strip()
        item_id = it.get("item_id")
        poly = it.get("poly")

        if status == "exact":
            menu_name = it.get("menu") or it.get("menu_name")
            evidence = {
                "menu_id": it.get("menu_id"),
                "ingredients_ko": it.get("ingredients_ko") or [],
                "alg_tags": it.get("alg_tags") or [],
            }
        elif status == "close":
            menu_name = it.get("decided_menu") or it.get("menu_name")
            evidence = {
                "menu_id": None,
                "ingredients_ko": [],
                "alg_tags": [],
            }
        else:
            continue

        if not item_id or not menu_name or poly is None:
            continue

        out.append(
            {
                "item_id": item_id,
                "status": status,
                "menu_name": str(menu_name),
                "poly": poly,
                "evidence": evidence,
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Step05: LLM menu explain + safety (Gemini-2.5-flash)")
    p.add_argument("--run_id", required=True, help="Run id under <data_dir>/runs/<run_id>/...")
    p.add_argument(
        "--data_dir",
        required=True,
        help=r"Base data directory (e.g. C:\Users\201\Desktop\PGHfolder\haenet\AI\menu_assistant\data)",
    )
    p.add_argument("--user_profile_json", default="", help="Optional: path to user profile JSON")
    p.add_argument("--include_debug", action="store_true", help="Save prompt/raw snapshots")
    p.add_argument("--max_retries", type=int, default=2, help="Max retries when schema validation fails")
    p.add_argument("--require_poly", action="store_true", help="Require poly for all kept items (recommended)")
    p.add_argument("--no_require_poly", action="store_true", help="Do not require poly (debug only)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    data_dir = Path(args.data_dir)
    run_dir = _resolve_run_dir(data_dir, args.run_id)
    llm_dir = run_dir / "llm"

    # -------------------------
    # Load inputs
    # -------------------------
    rag_match_path = run_dir / "rag_match" / "rag_match.json"
    if not rag_match_path.exists():
        raise FileNotFoundError(f"rag_match.json not found: {rag_match_path}")

    rag_match_json = _read_json(rag_match_path)
    user_profile = _load_user_profile(args.user_profile_json)
    print("[DEBUG] loaded user_profile:", user_profile)
    # -------------------------
    # Decision rules (EXACT/CLOSE only) -> minimal items
    # -------------------------
    from menu_assistant.worker.worker_app.llm.services.decision_rules import DecisionRules

    require_poly = True
    if args.no_require_poly:
        require_poly = False
    elif args.require_poly:
        require_poly = True

    rules = DecisionRules(require_poly=require_poly)
    raw_items, rules_meta = rules.build_llm_items(rag_match_json)

    # Normalize to LLM-input friendly shape (menu_name + poly always present)
    llm_items = _normalize_llm_input_items(raw_items)

    llm_input_payload = {
        "schema_version": "v1",
        "run_id": args.run_id,
        "user_profile": user_profile,
        "items": llm_items,
    }
    llm_input_meta = {
        "run_id": args.run_id,
        "decision_rules": rules_meta,
        "kept_for_llm": len(llm_items),
    }

    _write_json(llm_dir / "llm_input.json", llm_input_payload)
    _write_json(llm_dir / "llm_input_meta.json", llm_input_meta)

    if not llm_items:
        # Nothing to send to LLM; stop early
        print(f"[STEP05] No items to send to LLM. saved: {llm_dir / 'llm_input.json'}")
        return

    expected_ids = [it["item_id"] for it in llm_items]

    # -------------------------
    # Build prompt
    # -------------------------
    from menu_assistant.worker.worker_app.llm.prompt_builder import build_step05_prompt

    prompt = build_step05_prompt(run_id=args.run_id, user_profile=user_profile, items=llm_items)
    system_msg = prompt["system"]
    user_msg_base = prompt["user"]

    # -------------------------
    # LLM call + parse/validate + retry
    # -------------------------
    from menu_assistant.worker.worker_app.llm.client import Gemini25FlashClient
    from menu_assistant.worker.worker_app.llm.parsers import (
        parse_and_validate_llm_output,
        build_retry_prompt_from_error,
        LLMParseError,
    )
    from menu_assistant.worker.worker_app.llm.services.schema import (
        validate_llm_output_against_input_ids,
    )

    client = Gemini25FlashClient()

    last_err: str = ""
    user_msg = user_msg_base

    for attempt in range(args.max_retries + 1):
        if args.include_debug:
            _write_text(llm_dir / "llm_prompt.txt", f"[SYSTEM]\n{system_msg}\n\n[USER]\n{user_msg}\n")

        raw = client.generate_json(system=system_msg, user=user_msg)

        if args.include_debug:
            _write_text(llm_dir / "llm_raw.txt", raw)

        try:
            obj = parse_and_validate_llm_output(raw)

            # Strong cross-check: output ids must match input ids
            ok_ids, msg_ids = validate_llm_output_against_input_ids(obj, expected_ids)
            if not ok_ids:
                raise LLMParseError(msg_ids)

            # Success
            out_path = llm_dir / "llm_output.json"
            _write_json(out_path, obj)

            print(f"[STEP05] run_id           = {args.run_id}")
            print(f"[STEP05] input            = {rag_match_path}")
            print(f"[STEP05] llm_input.json    = {llm_dir / 'llm_input.json'}")
            print(f"[STEP05] llm_output.json   = {out_path}")
            print(f"[STEP05] items_out         = {len(obj.get('items', []))}")
            return

        except Exception as e:
            last_err = str(e)
            if attempt >= args.max_retries:
                break
            # Append retry instruction (keep same system; add follow-up constraint)
            user_msg = user_msg_base + "\n\n" + build_retry_prompt_from_error(last_err)

    raise RuntimeError(f"[STEP05] LLM output invalid after retries. last_error={last_err}")


if __name__ == "__main__":
    main()
