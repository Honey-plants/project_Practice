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
    FINAL.JSON (STRICT FLAT SCHEMA, OPTION B: no 'ui')

    Output item schema (must match prompt_builder.py example):
      - item_id (str)
      - match_status ("exact" | "unknown")
      - menu_name_ko (str)
      - poly (list[list[float]])
      - menu_description_ko (str)
      - menu_description_en (str)   # step6 fills; step5 can be ""
      - risk_description_ko (str)
      - risk_description_en (str)   # step6 fills; step5 can be ""
      - risk_difficulty (int)       # exact: 0|1|2 / unknown: MUST be 3
      - user_risk_match (dict|None) # pass-through from decision_rules if exists
      - comment_ko (str)
      - comment_en (str)            # step6 fills; step5 can be ""
      - is_menu (str|None)          # only meaningful when src status unknown
      - drop_reason_ko (str|None)   # only when dropped/filtered

    Notes:
    - UI fields (tier/color/badge...) are intentionally NOT included (Option B).
    - Any extra keys are intentionally NOT produced (STRICT).
    """

    # Build maps
    in_map: Dict[str, Dict[str, Any]] = {
        it["item_id"]: it for it in llm_input_items if isinstance(it, dict) and it.get("item_id")
    }
    out_map: Dict[str, Dict[str, Any]] = {
        it["item_id"]: it for it in llm_output_items if isinstance(it, dict) and it.get("item_id")
    }

    final_items: List[Dict[str, Any]] = []
    dropped_items: List[Dict[str, Any]] = []

    for item_id in sorted(in_map.keys()):
        src = in_map[item_id]
        llm = out_map.get(item_id, {}) if isinstance(out_map.get(item_id, {}), dict) else {}

        # ----------------------------
        # 1) drop unknown non-menu
        # ----------------------------
        src_status = (src.get("status") or src.get("match_status") or "").lower().strip()
        is_menu = (llm.get("is_menu") or "").lower().strip()
        if src_status == "unknown" and is_menu in ("no", "false", "0"):
            dropped_items.append(
                {
                    "item_id": item_id,
                    "drop_reason_ko": llm.get("drop_reason_ko") or "",
                }
            )
            continue

        # ----------------------------
        # 2) match_status -> strict ("exact" | "unknown")
        # ----------------------------
        # src가 exact/close면 exact 유지
        if src_status in ("exact", "close"):
            match_status = "exact"
        else:
            # llm이 match_status를 줘도 strict schema는 exact/unknown만 허용
            llm_status = (llm.get("match_status") or "").lower().strip()
            match_status = "exact" if llm_status in ("exact", "llm_match") else "unknown"

        # ----------------------------
        # 3) core fields
        # ----------------------------
        menu_name_ko = (
            llm.get("menu_name_ko")
            or llm.get("menu_name")      # 혹시 LLM이 menu_name으로 준 경우
            or src.get("menu_name_ko")
            or src.get("menu_name")
            or ""
        )
        menu_name_en = llm.get("menu_name_en")
        if not isinstance(menu_name_en, str):
            menu_name_en = ""

        # 안전장치: 비어있으면 ko로라도 채워 스키마를 깨지 않게
        if not menu_name_en.strip():
            menu_name_en = ""

        poly = src.get("poly") or src.get("match", {}).get("poly")  # 혹시 src 구조가 다를 경우 대비

        # descriptions: step5는 ko 채우고 en은 빈 값 유지(번역은 step6)
        menu_description_ko = (llm.get("menu_description_ko") or "").strip()
        risk_description_ko = (llm.get("risk_description_ko") or "").strip()

        menu_description_en = (llm.get("menu_description_en") or "").strip()
        risk_description_en = (llm.get("risk_description_en") or "").strip()

        comment_ko = (llm.get("comment_ko") or "").strip()
        comment_en = (llm.get("comment_en") or "").strip()

        # ----------------------------
        # 4) risk_difficulty (strict rule)
        # ----------------------------
        # unknown이면 무조건 3, exact면 0|1|2 권장. 없으면 기본값 부여.
        rd = llm.get("risk_difficulty")
        if match_status == "unknown":
            risk_difficulty = 3
        else:
            # exact인데 모델이 안 주면 0으로 보수적 기본
            try:
                risk_difficulty = int(rd) if rd is not None else 0
            except Exception:
                risk_difficulty = 0
            # exact는 0~2로 clamp
            if risk_difficulty < 0:
                risk_difficulty = 0
            if risk_difficulty > 2:
                risk_difficulty = 2

        # ----------------------------
        # 5) user_risk_match (pass-through 우선)
        # ----------------------------
        user_risk_match = src.get("user_risk_match")
        if user_risk_match is None:
            user_risk_match = llm.get("user_risk_match")

        # ----------------------------
        # 6) finalize strict item
        # ----------------------------
        final_items.append(
            {
                "item_id": item_id,
                "match_status": match_status,
                "menu_name_ko": menu_name_ko,
                "menu_name_en": menu_name_en,
                "poly": poly,

                "menu_description_ko": menu_description_ko,
                "menu_description_en": menu_description_en,

                "risk_description_ko": risk_description_ko,
                "risk_description_en": risk_description_en,

                "risk_difficulty": risk_difficulty,
                "user_risk_match": user_risk_match,

                "comment_ko": comment_ko,
                "comment_en": comment_en,

                # unknown에서만 의미 있는 필드(그 외엔 None 유지)
                "is_menu": llm.get("is_menu"),
                "drop_reason_ko": llm.get("drop_reason_ko"),
            }
        )

    return {
        "schema_version": "v1",
        "run_id": run_id,
        "user_profile": user_profile,
        "items": final_items,
        "dropped_items": dropped_items,
    }
