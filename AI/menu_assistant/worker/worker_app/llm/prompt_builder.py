# menu_assistant/worker/worker_app/llm/prompt_builder.py  (선택: 분리 추천)
from __future__ import annotations

import json
from typing import Any, Dict


def build_step05_prompt(*, run_id: str, user_profile: Dict[str, Any], items: list[Dict[str, Any]]) -> Dict[str, str]:
    """
    Returns { "system": "...", "user": "..." }
    items: decision_rules에서 나온 정제 item들 기반으로,
          menu_name/poly가 이미 포함된 형태로 넣는 것을 권장
    """
    # 1) 모델이 따라야 할 출력 구조를 "정확히" 제시
    output_schema_example = {
        "schema_version": "v1",
        "run_id": run_id,
        "items": [
            {
                "item_id": "itm_0001",
                "menu_name": "예시메뉴",
                "poly": [[0, 0], [1, 0], [1, 1], [0, 1]],
                "menu_description_ko": "메뉴 설명 (한국어, 1~2문장)",
                "risk_description_ko": "사용자 상태와 비교한 위험성 설명 (한국어, 1~3문장)",
                "risk_level": "CAUTION",
                "reason_bullets": ["근거 1", "근거 2"],
                "confidence": 0.75,
            }
        ],
    }

    system = (
        "You are a strict JSON generator.\n"
        "You MUST output ONLY valid JSON.\n"
        "Do NOT include markdown fences.\n"
        "Do NOT include any extra keys beyond the required schema fields (optional keys allowed only if described).\n"
        "All Korean fields must be written in Korean.\n"
        "Risk must be based on provided user_profile and evidence.\n"
    )

    # 2) user 메시지에서 입력과 출력 구조를 함께 제공
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
        "- Fill menu_description_ko and risk_description_ko.\n"
        "- risk_level must be one of OK, CAUTION, NO.\n"
        "- confidence must be between 0.0 and 1.0.\n"
        "- If uncertain, use CAUTION.\n"
    )

    return {"system": system, "user": user}
