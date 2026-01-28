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


# ============================================================
# Step06: Translate (execution-only)
# - Input  : final.json (from Step05 output)
# - Output : translate/translate.json (per-item translated payloads)
#            + final/final_translated.json (final.json에 번역 결과 merge)
# ============================================================


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"[step06] JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _infer_run_dir(data_dir: Path, run_id: str, run_dir: Optional[Path]) -> Path:
    if run_dir is not None:
        return run_dir
    return data_dir / "runs" / run_id


def _infer_final_json_path(run_dir: Path, input_final: Optional[Path]) -> Path:
    """
    우선순위:
      1) --input_final
      2) {run_dir}/final/final.json
      3) {run_dir}/final.json
    """
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
    """
    final.json이 어떤 형태로 오든 items 리스트를 뽑는다.
    반환:
      - items: List[dict]
      - container: dict (원본 dict이면 그 dict, 리스트이면 새 wrapper dict)
      - mode: "dict_items" | "list"
    """
    if isinstance(final_obj, dict):
        if isinstance(final_obj.get("items"), list):
            return final_obj["items"], final_obj, "dict_items"
        raise ValueError("[step06] final.json is dict but missing 'items' list.")
    if isinstance(final_obj, list):
        wrapper = {"items": final_obj}
        return wrapper["items"], wrapper, "list"
    raise ValueError(f"[step06] Unsupported final.json type: {type(final_obj)}")


def _merge_translation_into_final_item(
    *,
    item: Dict[str, Any],
    translated: Dict[str, Any],
) -> Dict[str, Any]:
    """
    item_id/match는 그대로 유지.
    번역 필드는 final item에 merge:
      - item.menu.menu_name_en
      - item.menu.menu_description_en
      - item.risk.risk_description_en
      - item.risk.comment_en   (기존 risk.comment(ko)는 유지)
    """
    item.setdefault("menu", {})
    item.setdefault("risk", {})

    menu_t = (translated.get("menu") or {}) if isinstance(translated, dict) else {}
    risk_t = (translated.get("risk") or {}) if isinstance(translated, dict) else {}

    item["menu"]["menu_name_en"] = (menu_t.get("menu_name_en") or "").strip()
    item["menu"]["menu_description_en"] = (menu_t.get("menu_description_en") or "").strip()

    item["risk"]["risk_description_en"] = (risk_t.get("risk_description_en") or "").strip()
    item["risk"]["comment_en"] = (translated.get("comment_en") or "").strip()

    return item


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
            return client.translate_final_item(
                item=item,
                system_prompt=system_p,
                user_prompt=user_p,
            )
        except Exception as e:
            last_err = e
            if attempt >= max_retries:
                break
            time.sleep(sleep_base * (attempt + 1))
    raise RuntimeError(f"[step06] Translation failed after retries: {last_err}") from last_err


def main() -> None:
    parser = argparse.ArgumentParser(description="Step06: Translate final.json fields using Gemini")
    parser.add_argument("--run_id", type=str, default=None, help="run id (e.g. 20260127_122120)")
    parser.add_argument("--data_dir", type=str, default="menu_assistant/data", help="base data dir")
    parser.add_argument("--run_dir", type=str, default=None, help="override run directory")
    parser.add_argument("--input_final", type=str, default=None, help="override input final.json path")

    # Step5와 동일 설정 공유: model/api_key_env
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Gemini model name")
    parser.add_argument("--api_key_env", type=str, default="GEMINI_API_KEY", help="API key env var name")

    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--top_k", type=int, default=40)

    # .env 로딩(선택): client.py는 기본적으로 상위 탐색을 하므로 보통 불필요
    parser.add_argument("--dotenv_path", type=str, default=None, help="explicit .env path (optional)")
    parser.add_argument("--max_dotenv_up", type=int, default=8, help="how many dirs to search upward for .env")

    parser.add_argument("--max_retries", type=int, default=2)
    parser.add_argument("--sleep_base", type=float, default=0.7)

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if args.run_id is None and args.run_dir is None:
        raise SystemExit("[step06] Either --run_id or --run_dir must be provided.")

    run_dir = _infer_run_dir(data_dir, args.run_id or "", Path(args.run_dir) if args.run_dir else None)
    input_final = Path(args.input_final) if args.input_final else None
    final_path = _infer_final_json_path(run_dir, input_final)

    print(f"[RUN] step_06_translate")
    print(f"[RUN] run_dir    = {run_dir}")
    print(f"[RUN] final.json = {final_path}")

    final_obj = _load_json(final_path)
    items, container, mode = _extract_items(final_obj)

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

        # 요구사항: item_id, match는 그대로; menu/risk/comment는 번역 필수
        if it.get("item_id") is None:
            raise ValueError(f"[step06] items[{idx}] missing item_id.")
        if it.get("match") is None:
            raise ValueError(f"[step06] items[{idx}] missing match.")
        if not isinstance(it.get("menu"), dict):
            it["menu"] = {}
        if not isinstance(it.get("risk"), dict):
            it["risk"] = {}

        translated = _translate_with_retries(
            client=client,
            item=it,
            max_retries=int(args.max_retries),
            sleep_base=float(args.sleep_base),
        )
        translated_rows.append(translated)

        merged = _merge_translation_into_final_item(item=it, translated=translated)
        merged_items.append(merged)

        print(
            f"[OK] idx={idx:04d} item_id={it.get('item_id')} match={it.get('match')} "
            f"menu_en='{merged.get('menu', {}).get('menu_name_en', '')[:30]}'"
        )

    out_translate = run_dir / "translate" / "translate.json"
    _save_json(out_translate, {"items": translated_rows})

    out_final_translated = run_dir / "final" / "final_translated.json"
    container["items"] = merged_items
    _save_json(out_final_translated, container)

    print(f"[SAVE] {out_translate}")
    print(f"[SAVE] {out_final_translated}")


if __name__ == "__main__":
    main()

r"""
python -m menu_assistant.worker.worker_app.pipeline.steps.step_06_translate ^
  --run_id 20260127_142946 ^
  --data_dir C:\Users\201\Desktop\PGHfolder\haenet\AI\menu_assistant\data
"""