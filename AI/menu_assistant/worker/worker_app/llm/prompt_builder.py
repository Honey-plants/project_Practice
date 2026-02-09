from __future__ import annotations

import json
from typing import Any, Dict, List


def build_step05_prompt(*, run_id: str, user_profile: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Step05 Prompt Builder (STRICT SCHEMA-DRIVEN)
    NOTE: Step05는 unknown items만 LLM에 보낸다는 전제(속도 최적화 B안).
    """

    # ✅ unknown-only 예시로 축소 (토큰 절감 + 혼선 감소)
    output_schema_example = {
        "schema_version": "v1",
        "run_id": run_id,
        "items": [
            {
                "item_id": "itm_0001",
                "match_status": "unknown",

                "menu_name_ko": "입력의 menu_name을 그대로 복사",
                "menu_name_en": "",
                "poly": [[0, 0], [1, 0], [1, 1], [0, 1]],

                "menu_description_ko": "메뉴 설명 정보가 제한적입니다. 주문 전 구성 재료를 확인하세요.",
                "menu_description_en": "",

                "risk_description_ko": "사용자 알러지/종교/기피 식품과의 충돌 가능성이 있어 주문 전 재료 확인이 필요합니다.",
                "risk_description_en": "",

                "risk_difficulty": 3,

                "user_risk_match": {
                    "allergy_tag_hits": None,
                    "religion_hit": None,
                    "avoid_food_hits": None,
                    "has_any_match": False,
                    "source": "unknown"
                },

                "comment_ko": "이 항목이 실제 메뉴라면, 알러지 유발 성분이 포함되나요?",
                "comment_en": "",

                "is_menu": "yes",
                "drop_reason_ko": None
            }
        ]
    }

    # ✅ unknown-only 호출 전제로 시스템 규칙도 축소/정렬
    system = (
        "You are a strict JSON generator.\n"
        "Output ONLY valid JSON. No markdown, no explanations.\n"
        "Do NOT include any keys not defined in the schema.\n\n"

        "SCHEMA ENFORCEMENT:\n"
        "- Output MUST exactly match the provided schema structure.\n"
        "- Missing required fields or extra fields are NOT allowed.\n"
        "- All *_ko fields MUST be Korean.\n\n"

        "IMPORTANT:\n"
        "- All input items are match_status='unknown'.\n"
        "- Therefore risk_difficulty MUST be EXACTLY 3 for ALL items.\n\n"

        "NON-EMPTY REQUIRED TEXT FIELDS:\n"
        "- menu_description_ko: non-empty Korean string.\n"
        "- risk_description_ko: non-empty Korean string.\n"
        "- comment_ko: non-empty Korean question ending with '?'.\n"
        "- If insufficient information, use conservative generic text.\n\n"

        "UNKNOWN MENU DETECTION:\n"
        "- You MUST decide whether the text is an actual orderable menu item.\n"
        "- Set is_menu to 'yes' or 'no'.\n"
        "- If is_menu='no', drop_reason_ko MUST be a non-empty Korean string.\n"
        "- Set is_menu='no' for size/option/notice such as:\n"
        "  '곱배기', '추가', '사리', '대/중/소', '리필', '공지', '안내', '이벤트', '원산지'.\n\n"

        "USER_RISK_MATCH RULES:\n"
        "- user_risk_match MUST be present for ALL items.\n"
        "- user_risk_match.source MUST be 'unknown'.\n"
        "- allergy_tag_hits / avoid_food_hits MUST be list[str] or null.\n"
        "- religion_hit MUST be string or null.\n"
        "- has_any_match MUST be boolean.\n\n"

        "SAFETY:\n"
        "- Do NOT invent ingredients or allergen tags.\n"
        "- Use ONLY provided user_profile and item evidence.\n\n"

        "COPY RULES:\n"
        "- Output exactly one item per input item.\n"
        "- item_id and poly MUST be copied exactly from input.\n"
        "- menu_name_ko MUST be copied from input.menu_name.\n"
        "- comment_en / menu_description_en / risk_description_en MUST be empty strings.\n"
    )

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

    return {"system": system, "user": user}
