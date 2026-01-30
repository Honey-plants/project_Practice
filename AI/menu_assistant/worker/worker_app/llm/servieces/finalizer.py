# menu_assistant/worker/worker_app/services/finalizer.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from menu_assistant.worker.worker_app.services.decision_rules import DecisionRules


def _item_id_to_int(item_id: str) -> int:
    # "itm_0007" -> 7 (sorting stable)
    try:
        return int(item_id.split("_")[-1])
    except Exception:
        return 10**9


def build_llm_payload_from_rag_match(
    *,
    run_id: str,
    rag_match_json: Dict[str, Any],
    user_profile: Dict[str, Any],
    rules: DecisionRules | None = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rules = rules or DecisionRules(require_poly=True)
    items, rules_meta = rules.build_llm_items(rag_match_json)

    payload = {
        "schema_version": "v1",
        "run_id": run_id,
        "user_profile": user_profile or {},
        "items": items,  # <- each item already contains item_id + poly + minimal fields
    }
    meta = {"run_id": run_id, "decision_rules": rules_meta}
    return payload, meta


def merge_to_final_output(
    *,
    run_id: str,
    user_profile: Dict[str, Any],
    llm_items_input: List[Dict[str, Any]],
    llm_items_result: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    핵심: item_id 기준으로 match/menu/risk를 한 덩어리로 묶어서 FinalOutput 생성.

    - llm_items_input: decision_rules로 만든 정제 입력 items (exact/close, poly 포함)
    - llm_items_result: LLM이 반환한 결과 items (item_id + menu_description_ko + risk_*)
    """

    # 1) input items를 item_id 맵으로
    in_map: Dict[str, Dict[str, Any]] = {}
    for it in llm_items_input:
        iid = str(it.get("item_id", "")).strip()
        if iid:
            in_map[iid] = it

    # 2) LLM result를 item_id 맵으로
    out_map: Dict[str, Dict[str, Any]] = {}
    for it in llm_items_result:
        iid = str(it.get("item_id", "")).strip()
        if iid:
            out_map[iid] = it

    # 3) item_id 기준으로 join (input에 있는 item_id만 최종 출력 대상으로 삼는 것을 권장)
    final_items: List[Dict[str, Any]] = []
    for item_id in sorted(in_map.keys(), key=_item_id_to_int):
        src = in_map[item_id]
        llm = out_map.get(item_id)

        # --- match 구성 (poly 필수) ---
        status = str(src.get("status", "")).lower()  # exact|close
        poly = src.get("poly")

        match: Dict[str, Any] = {
            "status": status,
            "poly": poly,
        }

        # exact: evidence 추가
        if status == "exact":
            match["menu_id"] = src.get("menu_id")
            match["ingredients_ko"] = src.get("ingredients_ko", []) or []
            match["alg_tags"] = src.get("alg_tags", []) or []

        # close: decided_menu trace
        if status == "close":
            match["decided_menu"] = src.get("decided_menu")

        # --- menu 구성 (최종 메뉴명은 코드가 결정) ---
        if status == "exact":
            menu_name_ko = src.get("menu", "")
        else:
            menu_name_ko = src.get("decided_menu", "")

        menu_description_ko = ""
        risk_level = "CAUTION"
        risk_explanation = ""
        reason_bullets: List[str] = []
        confidence = 0.0

        # --- risk / description은 LLM 결과에서 채움 ---
        # LLM이 아직 없거나 실패한 경우에도 필수 필드가 비지 않도록 기본값 세팅
        if isinstance(llm, dict):
            menu_description_ko = str(llm.get("menu_description_ko") or "").strip() or menu_description_ko
            risk_level = llm.get("risk_level") or llm.get("decision") or risk_level
            risk_explanation = str(llm.get("risk_explanation") or "").strip() or risk_explanation
            rb = llm.get("reason_bullets")
            if isinstance(rb, list):
                reason_bullets = [str(x) for x in rb if str(x).strip()]
            conf = llm.get("confidence", confidence)
            try:
                confidence = float(conf)
            except Exception:
                confidence = confidence

        # 필수 필드 보정: 메뉴 설명/위험 설명이 비면 운영에서 곤란하므로 최소 문구라도 넣기
        if not str(menu_description_ko).strip():
            menu_description_ko = f"{menu_name_ko}에 대한 설명입니다. (LLM 결과 누락)"
        if not str(risk_explanation).strip():
            risk_explanation = "사용자 프로필 정보와 비교한 위험성 평가를 생성하지 못했습니다. (LLM 결과 누락)"

        final_items.append(
            {
                "item_id": item_id,
                "match": match,
                "menu": {
                    "menu_name_ko": menu_name_ko,
                    "menu_description_ko": menu_description_ko,
                    "menu_name_en": "",
                    "menu_description_en": "",
                },
                "risk": {
                    "risk_level": risk_level,
                    "risk_explanation": risk_explanation,
                    "reason_bullets": reason_bullets,
                    "confidence": confidence,
                },
            }
        )

    return {
        "schema_version": "v1",
        "run_id": run_id,
        "user_profile": user_profile or {"allergy_tags": [], "avoid_foods": [], "religion": None},
        "items": final_items,
    }
