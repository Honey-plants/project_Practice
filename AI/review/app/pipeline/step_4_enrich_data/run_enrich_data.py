import re
from typing import Dict, Optional
from AI.review.app.pipeline.step_4_enrich_data.translate_menu import translate_to_en
from AI.review.app.pipeline.step_4_enrich_data.naverApi_search import find_store_by_query
from AI.review.app.pipeline.step_4_enrich_data.search_store_candidate import extract_store_name_candidates

def is_reasonable_match(query: str, result_name: str) -> bool:
    q = re.sub(r'\s+', '', query)
    r = re.sub(r'\s+', '', result_name)

    # 최소 부분 일치
    return q in r or r in q

def enrich_data(
    *,
    phone: Optional[str],
    lines: list[str],
    menu_ko: list[str],
    naver_cfg: Dict,
    gemini_api_key: str,
) -> Dict:
    store = None

    #  둘 다 지원 (NAVER_* / client_*)
    client_id = (naver_cfg or {}).get("NAVER_CLIENT_ID") or (naver_cfg or {}).get("client_id")
    client_secret = (naver_cfg or {}).get("NAVER_CLIENT_SECRET") or (naver_cfg or {}).get("client_secret")

    # 1) phone search
    if phone:
        store = find_store_by_query(phone, client_id=client_id, client_secret=client_secret)

    # 2) store가 None일 때만 후보군 뽑고 name search
    if store is None:
        candidates = extract_store_name_candidates(lines, top_k=10, max_candidates=5)
        for cand in candidates:
            store = find_store_by_query(cand, client_id=client_id, client_secret=client_secret)
            if store:
                break

    texts_to_translate = []
    if store:
        texts_to_translate.append(store["name_ko"])
    texts_to_translate.extend(menu_ko)

    translations = translate_to_en(
        texts_to_translate,
        api_key=gemini_api_key,
    )

    return {
        "store": {
            **store,
            "name_en": translations.get(store["name_ko"]) if store else None,
        } if store else None,

        "menu": [
            {
                "name_ko": m,
                "name_en": translations.get(m),
            }
            for m in menu_ko
        ],
    }