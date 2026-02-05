# menu_assistant/worker/worker_app/translate/prompt.py
from __future__ import annotations

import json
from typing import Any, Dict, Tuple


# ============================================================
# Prompt builder for Step6 translation (final.json item 기반)
# - 입력: final.json item (원본 그대로)
# - 출력: (system_prompt, user_prompt)
# - 모델 응답은 반드시 JSON (application/json) 형태
#
# 루트 스키마 번역 대상:
#   - menu_description_ko -> menu_description_en
#   - risk_description_ko -> risk_description_en
#   - comment_ko          -> comment_en
#
# 스키마 외 키는 절대 출력 금지
# ============================================================

_JSON_SCHEMA_HINT_BASE = {
    "menu_description_en": "string",
    "risk_description_en": "string",
    "comment_en": "string",
}

_JSON_SCHEMA_HINT_WITH_NAME = {
    **_JSON_SCHEMA_HINT_BASE,
    "menu_name_en": "string",
}


def build_translate_prompts_for_final_item(
    item: Dict[str, Any],
    *,
    include_menu_name: bool = False,
) -> Tuple[str, str]:
    """
    Step6에서 final.json의 item(1개)을 받아 Gemini 호출용 system/user prompt 생성.
    루트 스키마만 사용한다.
    """
    src = {
        "menu_name_ko": (item.get("menu_name_ko") or "").strip(),
        "menu_description_ko": (item.get("menu_description_ko") or "").strip(),
        "risk_description_ko": (item.get("risk_description_ko") or "").strip(),
        "comment_ko": (item.get("comment_ko") or "").strip(),
    }
    output_schema = _JSON_SCHEMA_HINT_WITH_NAME if include_menu_name else _JSON_SCHEMA_HINT_BASE
    required_key_count = 4 if include_menu_name else 3
    required_keys_text = (
        "menu_name_en, menu_description_en, risk_description_en, comment_en"
        if include_menu_name
             else "menu_description_en, risk_description_en, comment_en"
                    )
    system_prompt = (
        "You are a translation engine for a Korean restaurant menu safety assistant.\n"
        "Translate Korean to natural, clear English for end-users.\n"
        "You MUST output ONLY valid JSON (no markdown, no code fences).\n"
        "You MUST NOT output any keys that are not in the output_schema.\n"
        "Never invent ingredients, allergens, or restrictions not present in the source.\n"
        "If a source field is empty, output an empty string for the corresponding English field.\n"
        f"You MUST return a JSON object with EXACTLY {required_key_count} keys:\n"
        f"{required_keys_text}.\n"
        "Return ONLY these keys. Do NOT include item_id, match, menu, risk, comment, or any other keys.\n"
        "If you include extra keys, the output is invalid.\n"

    )

    user_payload = {
        "task": "Translate the Korean fields to English.",
        "source": src,
        "output_schema": output_schema,
        "rules": [
            "Return ONLY JSON matching output_schema exactly.",
            "Do NOT include any other keys.",
            "Keep translations concise, user-friendly, and faithful.",
            "comment_en must be a SINGLE natural English question.",
            "menu_name_en must be a SHORT dish name (not a full sentence).",

        ],
        "output_example": {
            "menu_name_en": "Chilled Buckwheat Noodles" if include_menu_name else None,
            "menu_description_en": "English menu description",
            "risk_description_en": "English risk description",
            "comment_en": "A single English yes/no question?"
        }

    }
    # output_example에서 menu_name_en None 제거(깔끔하게)

    if not include_menu_name:
        user_payload["output_example"].pop("menu_name_en", None)

    user_prompt = json.dumps(user_payload, ensure_ascii=False, indent=2)
    return system_prompt, user_prompt
