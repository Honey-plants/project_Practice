from __future__ import annotations

from typing import Any, Dict, List


def merge_llm_output_to_final(
    *,
    run_id: str,
    user_profile: Dict[str, Any],
    llm_input_items: List[Dict[str, Any]],
    llm_output_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Merge by item_id.
    LLM output schema (required):
      item_id, menu_name, poly, menu_description_ko, risk_description_ko
    """

    in_map = {it["item_id"]: it for it in llm_input_items if "item_id" in it}
    out_map = {it["item_id"]: it for it in llm_output_items if "item_id" in it}

    final_items: List[Dict[str, Any]] = []

    for item_id in sorted(in_map.keys()):
        src = in_map[item_id]
        llm = out_map.get(item_id, {})

        final_items.append(
            {
                "item_id": item_id,
                "match": {
                    "status": src.get("status"),
                    "poly": src.get("poly"),
                    "menu_id": src.get("menu_id"),
                    "ingredients_ko": src.get("ingredients_ko", []),
                    "alg_tags": src.get("alg_tags", []),
                    "decided_menu": src.get("decided_menu"),
                },
                "menu": {
                    "menu_name_ko": src.get("menu_name"),
                    "menu_description_ko": llm.get("menu_description_ko", ""),
                    "menu_name_en": "",
                    "menu_description_en": "",
                },
                "risk": {
                    "risk_level": llm.get("risk_level", "CAUTION"),
                    "risk_description_ko": llm.get("risk_description_ko", ""),
                    "reason_bullets": llm.get("reason_bullets", []),
                    "confidence": llm.get("confidence", 0.0),
                    "matched_constraints": llm.get("matched_constraints"),
                    "comment": llm.get("comment", ""),
                },
            }
        )

    return {
        "schema_version": "v1",
        "run_id": run_id,
        "user_profile": user_profile,
        "items": final_items,
    }
