from __future__ import annotations

import json
from typing import Any, Dict


def build_step05_prompt(*, run_id: str, user_profile: Dict[str, Any], items: list[Dict[str, Any]]) -> Dict[str, str]:
    """
    Returns { "system": "...", "user": "..." }
    items: decision_rules에서 나온 정제 item들 기반으로,
          menu_name/poly가 이미 포함된 형태
    """

    # Allowed ALG tags (UI/데이터 기준 고정)
    allowed_alg_tags = [
        "ALG_CELERY",
        "ALG_CEREALS_GLUTEN",
        "ALG_CRUSTACEANS",
        "ALG_EGGS",
        "ALG_FISH",
        "ALG_MILK",
        "ALG_MOLLUSCS",
        "ALG_MUSTARD",
        "ALG_SESAME",
        "ALG_SOY",
        "ALG_TREE_NUTS",
    ]

    # 1) 출력 JSON 구조 예시 (스키마 고정 + matched_constraints 확장)
    # - NOTE: schema.py validator는 REQUIRED 5개 + OPTIONAL 일부만 엄격 검증하며,
    #   추가 필드는 허용되는 정책이므로(unknown key reject 없음) 확장 가능. :contentReference[oaicite:1]{index=1}
    output_schema_example = {
        "schema_version": "v1",
        "run_id": run_id,
        "items": [
            {
                "item_id": "itm_0001",
                "menu_name": "예시메뉴",
                "poly": [[0, 0], [1, 0], [1, 1], [0, 1]],
                "menu_description_ko": "메뉴 설명 (한국어, 1~2문장)",
                "risk_description_ko": (
                    "위험: CAUTION — 알러지 또는 식이 제한과 일부 충돌 가능성이 있습니다.\n"
                    "근거: 제공된 재료 정보 또는 알러지 태그를 기준으로 판단했습니다.\n"
                    "권고: 주문 전 원재료와 소스 구성을 매장에 확인하는 것이 좋습니다."
                ),
                "risk_level": "CAUTION",
                "reason_bullets": [
                    "사용자 조건(알러지/종교/비선호)과 메뉴 근거(evidence: alg_tags/ingredients_ko) 간 충돌 가능성"
                ],
                "confidence": 0.75,

                # NEW: 사용자 조건과 메뉴 근거가 충돌한다고 판단되는 항목 표시
                # - 없으면 반드시 null
                # - allergy_tags는 allowed_alg_tags 중에서만 선택
                "matched_constraints": {
                    "allergy_tags": ["ALG_MILK"],
                    "religion": None,
                    "avoid_foods": None,
                },
            }
        ],
    }

    # 2) system 메시지 (행동 규칙 + 톤 강제 + matched_constraints 규칙)
    system = (
        "You are a strict JSON generator.\n"
        "You MUST output ONLY valid JSON.\n"
        "Do NOT include markdown fences.\n"
        "Do NOT include any explanatory text outside JSON.\n"
        "All Korean fields must be written in Korean.\n\n"
        "Risk judgment rules:\n"
        "- Risk must be determined ONLY using provided user_profile and item evidence.\n"
        "- Do NOT invent ingredients or allergies.\n"
        "- Use the following risk levels ONLY: OK, CAUTION, NO.\n"
        "- If evidence is insufficient or ambiguous, choose CAUTION.\n\n"
        "Constraint checking rules (IMPORTANT):\n"
        "- You MUST check whether the menu might conflict with user_profile constraints using only:\n"
        "  (A) evidence.alg_tags, evidence.ingredients_ko, menu_name\n"
        "  (B) user_profile.allergy_tags, user_profile.avoid_foods, user_profile.religion\n"
        "- If you 판단 that any conflict MAY exist, you MUST reflect it in:\n"
        "  1) matched_constraints\n"
        "  2) risk_level\n"
        "  3) reason_bullets and risk_description_ko\n\n"
        "Allowed allergy tag list:\n"
        f"- allergy_tags MUST be a subset of: {', '.join(allowed_alg_tags)}\n\n"
        "matched_constraints rules:\n"
        "- matched_constraints must be an object with keys: allergy_tags, religion, avoid_foods\n"
        "- allergy_tags: list of matching ALG_* tags IF relevant; otherwise null\n"
        "- religion: a short string explaining the relevant religion constraint hit (e.g., '돼지고기/알코올 가능') IF relevant; otherwise null\n"
        "- avoid_foods: list of user avoid foods found/possibly found IF relevant; otherwise null\n"
        "- Do NOT put empty list; use null when there is no relevant match.\n\n"
        "Risk description writing rules:\n"
        "- risk_description_ko MUST consist of EXACTLY 3 sentences, in the following order:\n"
        "  1) '위험: <OK|CAUTION|NO> — 한 줄 요약'\n"
        "  2) '근거: 판단 근거 설명 (알러지 태그, 재료, 조리 특성 등)'\n"
        "  3) '권고: 사용자 행동 지침 (주문 전 확인, 주의, 대체 제안 등)'\n"
        "- If evidence.alg_tags contains any 'ALG_*', you MUST explicitly mention '알러지' in the 근거 sentence.\n"
        "- If matched_constraints.allergy_tags is not null, risk_level should be NO or CAUTION depending on certainty.\n"
        "- If risk_level is NO, 권고 문장은 섭취 회피 또는 주문 전 확인을 명확히 포함해야 합니다.\n"
        "- Keep tone calm, practical, and suitable for an MVP food safety assistant.\n"
    )

    # 3) user 메시지 (입력 + 출력 구조 + 규칙 강화)
    user = (
        "Given the following input, produce the output JSON that matches EXACTLY the structure below.\n\n"
        "[OUTPUT JSON STRUCTURE]\n"
        f"{json.dumps(output_schema_example, ensure_ascii=False, indent=2)}\n\n"
        "[INPUT]\n"
        f"run_id: {run_id}\n"
        f"user_profile: {json.dumps(user_profile, ensure_ascii=False)}\n"
        f"items: {json.dumps(items, ensure_ascii=False)}\n\n"
        "Rules:\n"
        "- For each input item, output exactly one item in output.items with the same item_id.\n"
        "- Copy item_id, menu_name, poly EXACTLY from input items.\n"
        "- menu_description_ko should briefly explain what the menu is.\n"
        "- You MUST evaluate whether the menu may violate user constraints (allergy/religion/avoid_foods) using evidence.\n"
        "- If any potential match exists, fill matched_constraints accordingly; otherwise set each field to null.\n"
        "- risk_description_ko must follow the 3-sentence template defined above.\n"
        "- risk_level must be consistent with risk_description_ko and matched_constraints.\n"
        "- reason_bullets must include the specific matched constraint when present (e.g., 'ALG_MILK 가능성', '돼지고기 가능성').\n"
        "- confidence must be between 0.0 and 1.0.\n"
    )

    return {"system": system, "user": user}
