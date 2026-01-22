# menu_assistant/worker/worker_app/llm/parsers.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple, Optional

from menu_assistant.worker.worker_app.services.schema import validate_llm_output_v1


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


class LLMParseError(Exception):
    pass


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from raw text.
    - If the model outputs pure JSON, json.loads will work.
    - If extra text exists, try to find the largest {...} block.
    """
    text = (text or "").strip()
    if not text:
        raise LLMParseError("empty response")

    # 1) direct parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 2) regex block extraction
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        raise LLMParseError("no JSON object found in response")

    block = m.group(0)
    try:
        obj = json.loads(block)
    except Exception as e:
        raise LLMParseError(f"JSON parse failed: {e}") from e

    if not isinstance(obj, dict):
        raise LLMParseError("parsed JSON is not an object")
    return obj


def build_retry_prompt_from_error(err_msg: str) -> str:
    """
    This string is appended as a follow-up user message for retry.
    Keep it short and directive.
    """
    return (
        "Your previous output was invalid.\n"
        f"Validation error: {err_msg}\n"
        "Return ONLY valid JSON with ALL required fields:\n"
        "- schema_version, run_id, items\n"
        "- items[*].item_id, menu_name, poly, menu_description_ko, risk_description_ko\n"
        "Do NOT include markdown.\n"
        "Do NOT include any text outside JSON.\n"
    )


def parse_and_validate_llm_output(raw_text: str) -> Dict[str, Any]:
    obj = extract_json_object(raw_text)
    ok, msg = validate_llm_output_v1(obj)
    if not ok:
        raise LLMParseError(msg)
    # normalize schema_version default
    if obj.get("schema_version") is None:
        obj["schema_version"] = "v1"
    return obj
