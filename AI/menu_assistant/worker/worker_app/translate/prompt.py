# menu_assistant/worker/worker_app/translate/prompt.py
from __future__ import annotations

import json
from typing import Any, Dict, Tuple


# ============================================================
# Prompt builder for Step6 translation (final.json 기반)
# - 입력: final.json item (원본 그대로)
# - 출력: (system_prompt, user_prompt)
# - 모델 응답은 반드시 JSON (application/json) 형태로만 오게 유도
# ============================================================

_JSON_SCHEMA_HINT = {
    "menu": {
        "menu_name_en": "string",
        "menu_description_en": "string",
    },
    "risk": {
        "risk_description_en": "string",
    },
    "comment": {
    "comment_en": "string",
    "comment_ko": "string"}
}


def build_translate_prompts_for_final_item(item: Dict[str, Any]) -> Tuple[str, str]:
    """
    Step6에서 final.json의 item(1개)을 받아서
    Gemini 호출용 system/user prompt를 만든다.

    번역 필수:
      - menu.menu_name_ko        -> menu.menu_name_en
      - menu.menu_description_ko -> menu.menu_description_en
      - risk.risk_description_ko -> risk.risk_description_en
      - risk.comment             -> comment_en

    유지(번역하지 않음):
      - item_id, match (Step6에서 passthrough)
      - risk.risk_level (그대로 유지 권장)
    """
    # 원본에서 필요한 값만 안전하게 뽑기 (빈값 가능)
    item_id = item.get("item_id")
    match = item.get("match")

    menu = item.get("menu") or {}
    risk = item.get("risk") or {}

    src = {
        "item_id": item_id,
        "match": match,
        "menu": {
            "menu_name_ko": (menu.get("menu_name_ko") or "").strip(),
            "menu_description_ko": (menu.get("menu_description_ko") or "").strip(),
        },
        "risk": {
            "risk_level": (risk.get("risk_level") or "").strip(),
            "risk_description_ko": (risk.get("risk_description_ko") or "").strip(),
            "comment_ko": (risk.get("comment") or "").strip(),
        },
    }

    system_prompt = (
        "You are a translation engine for a Korean restaurant menu safety assistant.\n"
        "Translate Korean text to natural, clear English for end-users.\n"
        "You must output ONLY valid JSON (no markdown, no code fences, no extra keys).\n"
        "Keep meanings accurate, especially allergy/diet-related warnings.\n"
        "If a source field is empty, output an empty string for the corresponding English field.\n"
        "Never invent ingredients or allergens not present in the source.\n"
    )

    # user prompt는 최대한 구조화 + 강한 출력 제약
    user_payload = {
        "task": "Translate the following fields from Korean to English.and leave comment_ko as is korean",
        "source": src,
        "output_schema": _JSON_SCHEMA_HINT,
        "rules": [
            "Return ONLY JSON matching output_schema exactly.",
            "Do NOT include item_id, match, or risk_level in the output JSON (they are handled separately).",
            "menu_name_en should be short (menu name).",
            "Descriptions should be concise, user-friendly, and preserve safety meaning."
            "comment_ko must keep original and after translate put in comment_en",
        ],
    }

    user_prompt = json.dumps(user_payload, ensure_ascii=False, indent=2)
    return system_prompt, user_prompt
