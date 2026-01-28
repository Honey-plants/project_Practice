from typing import Dict
from AI.review.app.pipeline.step_4_enrich_data.translate_menu import translate_to_en
from AI.review.app.pipeline.step_4_enrich_data.naverApi_search import find_store_by_phone


def enrich_data(
    *,
    phone: str | None,
    menu_ko: list[str],
    naver_cfg: Dict,
    gemini_api_key: str,
) -> Dict:
    store = None
    if phone:
        store = find_store_by_phone(phone, **naver_cfg)

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