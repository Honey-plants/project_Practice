from __future__ import annotations

from typing import Any, Dict, List


def _build_ui(status: str) -> Dict[str, Any]:
    s = (status or "").lower().strip()
    if s in ("exact", "close"):
        return {
            "tier": "confirmed",
            "color": "red",
            "badge_ko": "확정",
            "badge_en": "Confirmed",
        }
    if s == "llm_match":
        return {
            "tier": "suggested",
            "color": "orange",
            "badge_ko": "추정",
            "badge_en": "Suggested",
        }
    return {
        "tier": "unknown",
        "color": "gray",
        "badge_ko": "미확인",
        "badge_en": "Unknown",
    }


def _pick_candidate(evidence: Dict[str, Any], selected_id: Any) -> Dict[str, Any]:
    """
    evidence.candidates에서 selected_candidate_id와 일치하는 후보를 반환
    """
    cands = evidence.get("candidates")
    if not isinstance(cands, list) or not selected_id:
        return {}
    sid = str(selected_id).strip()
    if not sid:
        return {}
    for c in cands:
        if not isinstance(c, dict):
            continue
        cid = c.get("id")
        if cid is not None and str(cid).strip() == sid:
            return c
    return {}


def merge_llm_output_to_final(
    *,
    run_id: str,
    user_profile: Dict[str, Any],
    llm_input_items: List[Dict[str, Any]],
    llm_output_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Merge by item_id.

    IMPORTANT:
    - For ambiguous/not_found items:
      - If LLM returns match_status='llm_match' and selected_candidate_id,
        we will COPY ingredients_ko/alg_tags/menu_id from the selected candidate ONLY.
      - Otherwise, keep them empty and set status to 'unknown'.
    """

    in_map = {it["item_id"]: it for it in llm_input_items if "item_id" in it}
    out_map = {it["item_id"]: it for it in llm_output_items if "item_id" in it}

    final_items: List[Dict[str, Any]] = []

    for item_id in sorted(in_map.keys()):
        src = in_map[item_id]
        llm = out_map.get(item_id, {})

        src_status = (src.get("status") or "").lower().strip()
        llm_status = (llm.get("match_status") or "").lower().strip()

        # ✅ 최종 status 결정
        final_status = src_status
        if src_status in ("ambiguous", "not_found"):
            if llm_status == "llm_match":
                final_status = "llm_match"
            else:
                final_status = "unknown"

        # ✅ 최종 메뉴명 결정 (LLM이 보강한 menu_name 우선)
        final_menu_name = llm.get("menu_name") or src.get("menu_name") or ""

        # ✅ 보강 항목은 후보 기반으로만 ingredients/alg_tags 채움
        evidence = src.get("evidence") if isinstance(src.get("evidence"), dict) else {}
        selected = _pick_candidate(evidence, llm.get("selected_candidate_id"))

        menu_id = src.get("menu_id")
        ingredients_ko = src.get("ingredients_ko", []) or []
        alg_tags = src.get("alg_tags", []) or []

        if final_status == "llm_match":
            # 후보에서만 채움 (LLM 생성 금지 정책)
            menu_id = selected.get("id") or menu_id
            ingredients_ko = selected.get("ingredients_ko") or []
            alg_tags = selected.get("alg_tags") or []

        # exact는 기존 그대로 유지 (already stable)
        if src_status == "exact":
            menu_id = src.get("menu_id")
            ingredients_ko = src.get("ingredients_ko", []) or []
            alg_tags = src.get("alg_tags", []) or []

        ui = _build_ui(final_status)

        final_items.append(
            {
                "item_id": item_id,

                "match": {
                    "status": final_status,
                    "poly": src.get("poly"),
                    "menu_id": menu_id,
                    "ingredients_ko": ingredients_ko,
                    "alg_tags": alg_tags,
                    "decided_menu": src.get("decided_menu"),
                    # (선택) 디버그/추적용
                    "source": "rag" if final_status in ("exact", "close") else ("llm" if final_status == "llm_match" else "unknown"),
                },

                "menu": {
                    "menu_name_ko": final_menu_name,
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
                    # (선택) 프론트에서 바로 쓰고 싶으면 유지
                    "comment_en": llm.get("comment_en", ""),
                },

                # ✅ 프론트 색상/배지용(추가 필드라 기존 화면 안 깨짐)
                "ui": ui,
            }
        )

    return {
        "schema_version": "v1",
        "run_id": run_id,
        "user_profile": user_profile,
        "items": final_items,
    }
