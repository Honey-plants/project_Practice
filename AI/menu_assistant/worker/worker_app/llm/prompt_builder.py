from __future__ import annotations

import json
from typing import Any, Dict, List


def build_step05_prompt(*, run_id: str, user_profile: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Step05 Prompt Builder (STRICT SCHEMA-DRIVEN)

    This prompt is strictly aligned with schema.py.
    The model MUST output ONLY schema-compliant JSON.
    Any parameter not defined in schema is FORBIDDEN.
    """

    # -------------------------------------------------
    # Output schema example (STRICT – schema aligned)
    # -------------------------------------------------
    output_schema_example = {
        "schema_version": "v1",
        "run_id": run_id,
        "items": [
            {
                "item_id": "itm_0001",
                "match_status": "exact",   # "exact" | "unknown"

                "menu_name_ko": "메뉴명",
                "menu_name_en": "enlgish menu name",
                "poly": [[0, 0], [1, 0], [1, 1], [0, 1]],

                "menu_description_ko": "메뉴에 대한 한국어 설명",
                "menu_description_en": "",

                "risk_description_ko": (
                    "위험: CAUTION — 사용자 조건과 일부 충돌 가능성이 있습니다.\n"
                    "근거: 알러지/종교/기피 식재료 정보를 기반으로 판단했습니다.\n"
                    "권고: 주문 전 매장에 재료 포함 여부를 확인하세요."
                ),
                "risk_description_en": "",

                "risk_difficulty": 0,      # exact: 0|1|2 / unknown: MUST be 3

                "user_risk_match": {
                    "allergy_tag_hits": ["ALG_MILK"],
                    "religion_hit": None,
                    "avoid_food_hits": None,
                    "has_any_match": True,
                    "source": "exact"
                },

                "comment_ko": "이 메뉴에 우유 또는 유제품이 들어가나요?",
                "comment_en": "",

                "is_menu": None,
                "drop_reason_ko": None
            }
        ]
    }

    # -------------------------------------------------
    # SYSTEM PROMPT (STRICT RULES)
    # -------------------------------------------------
    system = (
        "You are a strict JSON generator.\n"
        "You MUST output ONLY valid JSON.\n"
        "Do NOT include markdown, comments, or explanations.\n"
        "Do NOT include any keys that are not defined in the schema.\n\n"

        "SCHEMA ENFORCEMENT:\n"
        "- The output MUST exactly match the provided schema structure.\n"
        "- Any missing required field or extra field will cause a failure.\n"
        "- All Korean fields must be written in Korean.\n\n"
        
        "NON-EMPTY REQUIRED TEXT FIELDS:\n"
        "- menu_description_ko MUST be a non-empty Korean string.\n"
        "- risk_description_ko MUST be a non-empty Korean string.\n"
        "- comment_ko MUST be a non-empty Korean question ending with '?'.\n"
        "- If you do not have enough information, you MUST still write a conservative generic description.\n"
        "  Example fallback for menu_description_ko: '메뉴 설명 정보가 제한적입니다. 주문 전 구성 재료를 확인하세요.'\n"
        "  Example fallback for risk_description_ko: '사용자 알러지/종교/기피 식품과의 충돌 가능성이 있어 주문 전 재료 확인이 필요합니다.'\n"

        
        "MATCH STATUS RULES:\n"
        "- match_status MUST be either 'exact' or 'unknown'.\n"
        "- For match_status='exact':\n"
        "  - menu_name_ko MUST remain identical to input.menu_name.\n"
        "  - risk_difficulty MUST be one of 0, 1, or 2.\n"
        "- For match_status='unknown':\n"
        "  - risk_difficulty MUST be EXACTLY 3.\n"
        "  - You MUST decide whether this text is an actual orderable menu item.\n"
        "  - Set is_menu to 'yes' or 'no'.\n"
        "  - If is_menu='no', drop_reason_ko MUST be a non-empty Korean string.\n\n"

        "RISK_DIFFICULTY RULES (IMPORTANT):\n"
        "- risk_difficulty meanings:\n"
        "  0 = No match with allergy/religion/avoid_food.\n"
        "  1 = Only avoid_food matched.\n"
        "  2 = allergy_tag or religion matched (at least one).\n"
        "  3 = Unknown menu (forced, regardless of content).\n"
        "- You MUST NOT use risk_difficulty=3 for exact items.\n\n"

        "USER_RISK_MATCH RULES:\n"
        "- user_risk_match MUST be present for ALL items.\n"
        "- user_risk_match.source MUST be 'exact' or 'unknown'.\n"
        "- allergy_tag_hits / avoid_food_hits MUST be list[str] or null.\n"
        "- religion_hit MUST be string or null.\n"
        "- has_any_match MUST be boolean.\n\n"

        "SAFETY CONSTRAINTS:\n"
        "- You MUST NOT invent ingredients, alg_tags, or religion matches.\n"
        "- Use ONLY the provided user_profile and item evidence.\n"
        "- If information is insufficient, be conservative.\n\n"

        "COMMENT RULES:\n"
        "- comment_ko MUST be a SINGLE Korean question ending with '?'.\n"
        "- The question MUST be based on user's allergy/religion/avoid_food.\n"
        "- comment_en MUST be an empty string at this step.\n\n"
        "- If you are uncertain, comment_ko should ask to confirm allergens/ingredients with yes/no.\n"


        "UNKNOWN MENU DETECTION:\n"
        "- Set is_menu='no' for size/option/notice text such as:\n"
        "  '곱배기', '추가', '사리', '대/중/소', '리필', '공지', '안내', '이벤트', '원산지'.\n"
        "- Set is_menu='yes' ONLY if it is a real orderable dish.\n"
    )

    # -------------------------------------------------
    # USER PROMPT
    # -------------------------------------------------
    user = (
        "Generate output JSON that EXACTLY matches the schema below.\n\n"
        "[OUTPUT SCHEMA EXAMPLE]\n"
        f"{json.dumps(output_schema_example, ensure_ascii=False, indent=2)}\n\n"
        "[INPUT]\n"
        f"run_id: {run_id}\n"
        f"user_profile: {json.dumps(user_profile, ensure_ascii=False)}\n"
        f"items: {json.dumps(items, ensure_ascii=False)}\n\n"
        "RULES:\n"
        "- Output exactly one item per input item.\n"
        "- item_id and poly MUST be copied exactly from input.\n"
        "- Do NOT add or remove items.\n"
        "- Do NOT add extra fields.\n"
    )

    return {
        "system": system,
        "user": user,
    }
