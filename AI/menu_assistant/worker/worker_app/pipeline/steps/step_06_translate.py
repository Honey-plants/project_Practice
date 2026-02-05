# menu_assistant/worker/worker_app/pipeline/steps/step_06_translate.py
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from menu_assistant.worker.worker_app.llm.client import GeminiClientConfig
from menu_assistant.worker.worker_app.translate.model import GeminiTranslateClient
from menu_assistant.worker.worker_app.translate.prompt import build_translate_prompts_for_final_item
from menu_assistant.worker.worker_app.translate.schema import validate_translate_output


# ============================================================
# Step06: Translate (FLAT STRICT MODE)
# - Input  : run_dir/final/final.json   (Step05 strict-flat output)
# - Output : run_dir/translate/translate.json
#            run_dir/final/final_translated.json
#
# IMPORTANT:
#   Step05 final.json is STRICT-FLAT schema (no menu/risk/ui nesting).
#   This step reads *_ko from root and writes *_en to root only.
# ============================================================


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"[step06] JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _infer_run_dir(data_dir: Path, run_id: str, run_dir: Optional[Path]) -> Path:
    return run_dir if run_dir is not None else (data_dir / "runs" / run_id)


def _infer_final_json_path(run_dir: Path, input_final: Optional[Path]) -> Path:
    if input_final is not None:
        return input_final
    p1 = run_dir / "final" / "final.json"
    if p1.exists():
        return p1
    p2 = run_dir / "final.json"
    if p2.exists():
        return p2
    return p1


def _extract_items(final_obj: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
    if isinstance(final_obj, dict):
        if isinstance(final_obj.get("items"), list):
            return final_obj["items"], final_obj, "dict_items"
        raise ValueError("[step06] final.json is dict but missing 'items' list.")
    if isinstance(final_obj, list):
        wrapper = {"items": final_obj}
        return wrapper["items"], wrapper, "list"
    raise ValueError(f"[step06] Unsupported final.json type: {type(final_obj)}")


def _get_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list):
        parts = [str(x).strip() for x in v if str(x).strip()]
        return "\n".join(parts)
    return str(v).strip()


def _normalize_translation_output(obj: Any) -> Dict[str, Any]:
    """
    Accept either:
      A) strict output: {menu_description_en, risk_description_en, comment_en}
      B) legacy nested output: {menu{...}, risk{...}, comment{...}}
    Normalize to A.
    """
    if not isinstance(obj, dict):
        return {}

    if set(obj.keys()) == {"menu_description_en", "risk_description_en", "comment_en"}:
        return obj

    menu_en = ""
    risk_en = ""
    comment_en = ""

    m = obj.get("menu")
    if isinstance(m, dict):
        menu_en = _get_str(m.get("menu_description_en"))

    r = obj.get("risk")
    if isinstance(r, dict):
        risk_en = _get_str(r.get("risk_description_en"))

    c = obj.get("comment")
    if isinstance(c, dict):
        comment_en = _get_str(c.get("comment_en"))
    elif isinstance(obj.get("comment"), str):
        comment_en = _get_str(obj.get("comment"))

    return {
        "menu_description_en": menu_en,
        "risk_description_en": risk_en,
        "comment_en": comment_en,
    }


def _translate_with_retries(
    client: GeminiTranslateClient,
    item: Dict[str, Any],
    max_retries: int,
    sleep_base: float,
) -> Dict[str, Any]:
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            system_p, user_p = build_translate_prompts_for_final_item(item)

            out = client.translate_final_item(
                item=item,
                system_prompt=system_p,
                user_prompt=user_p,
            )
            out = _normalize_translation_output(out)

            ok, msg = validate_translate_output(out)
            if not ok:
                raise ValueError(f"[step06] Invalid translation output: {msg}")

            # ✅ HARD CHECK: KO가 있는데 EN이 비면 실패로 처리 (빈 번역 저장 방지)
            if _get_str(item.get("menu_description_ko")) and not _get_str(out.get("menu_description_en")):
                raise ValueError("[step06] empty menu_description_en while menu_description_ko exists")
            if _get_str(item.get("risk_description_ko")) and not _get_str(out.get("risk_description_en")):
                raise ValueError("[step06] empty risk_description_en while risk_description_ko exists")
            if _get_str(item.get("comment_ko")) and not _get_str(out.get("comment_en")):
                raise ValueError("[step06] empty comment_en while comment_ko exists")

            return out

        except Exception as e:
            last_err = e
            if attempt >= max_retries:
                break
            time.sleep(sleep_base * (attempt + 1))

    raise RuntimeError(f"[step06] Translation failed after retries: {last_err}") from last_err


def main() -> None:
    parser = argparse.ArgumentParser(description="Step06: Translate final.json fields (STRICT-FLAT)")
    parser.add_argument("--run_id", type=str, default=None)
    parser.add_argument("--data_dir", type=str, default="menu_assistant/data")
    parser.add_argument("--run_dir", type=str, default=None)
    parser.add_argument("--input_final", type=str, default=None)

    parser.add_argument("--model", type=str, default="gemini-2.5-flash")
    parser.add_argument("--api_key_env", type=str, default="GEMINI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--top_k", type=int, default=40)

    parser.add_argument("--dotenv_path", type=str, default=None)
    parser.add_argument("--max_dotenv_up", type=int, default=8)

    parser.add_argument("--max_retries", type=int, default=2)
    parser.add_argument("--sleep_base", type=float, default=0.7)

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if args.run_id is None and args.run_dir is None:
        raise SystemExit("[step06] Either --run_id or --run_dir must be provided.")

    run_dir = _infer_run_dir(data_dir, args.run_id or "", Path(args.run_dir) if args.run_dir else None)
    final_path = _infer_final_json_path(run_dir, Path(args.input_final) if args.input_final else None)

    print("[RUN] step_06_translate (STRICT-FLAT)")
    print(f"[RUN] run_dir    = {run_dir}")
    print(f"[RUN] final.json = {final_path}")

    final_obj = _load_json(final_path)
    items, container, _mode = _extract_items(final_obj)

    cfg = GeminiClientConfig(
        model=args.model,
        api_key_env=args.api_key_env,
        temperature=float(args.temperature),
        top_p=float(args.top_p),
        top_k=int(args.top_k),
        response_mime_type="application/json",
    )
    client = GeminiTranslateClient(
        cfg,
        dotenv_path=args.dotenv_path,
        max_dotenv_up=int(args.max_dotenv_up),
    )

    translated_rows: List[Dict[str, Any]] = []
    merged_items: List[Dict[str, Any]] = []

    for idx, it in enumerate(items):
        if not isinstance(it, dict):
            raise ValueError(f"[step06] items[{idx}] is not an object/dict.")
        if it.get("item_id") is None:
            raise ValueError(f"[step06] items[{idx}] missing item_id.")

        # flat KO only
        it["menu_description_ko"] = _get_str(it.get("menu_description_ko"))
        it["risk_description_ko"] = _get_str(it.get("risk_description_ko"))
        it["comment_ko"] = _get_str(it.get("comment_ko"))

        translated = _translate_with_retries(
            client=client,
            item=it,
            max_retries=int(args.max_retries),
            sleep_base=float(args.sleep_base),
        )

        # write EN to root only
        it["menu_description_en"] = _get_str(translated.get("menu_description_en"))
        it["risk_description_en"] = _get_str(translated.get("risk_description_en"))
        it["comment_en"] = _get_str(translated.get("comment_en"))

        translated_rows.append(
            {
                "item_id": it.get("item_id"),
                "menu_description_en": it["menu_description_en"],
                "risk_description_en": it["risk_description_en"],
                "comment_en": it["comment_en"],
            }
        )

        merged_items.append(it)

        print(
            f"[OK] idx={idx:04d} item_id={it.get('item_id')} "
            f"menu_en_len={len(it['menu_description_en'])} risk_en_len={len(it['risk_description_en'])}"
        )

    _save_json(run_dir / "translate" / "translate.json", {"items": translated_rows})
    container["items"] = merged_items
    _save_json(run_dir / "final" / "final_translated.json", container)

    print(f"[DONE] translate.json        = {run_dir / 'translate' / 'translate.json'}")
    print(f"[DONE] final_translated.json = {run_dir / 'final' / 'final_translated.json'}")


if __name__ == "__main__":
    main()
