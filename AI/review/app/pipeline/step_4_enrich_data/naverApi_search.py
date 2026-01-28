import requests
from typing import Optional, Dict


def find_store_by_phone(
    phone: str,
    *,
    client_id: str,
    client_secret: str,
) -> Optional[Dict]:

    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": phone,
        "display": 1,
    }

    r = requests.get(url, headers=headers, params=params, timeout=5)
    if r.status_code != 200:
        return None

    items = r.json().get("items")
    if not items:
        return None

    it = items[0]
    return {
        "name_ko": it["title"].replace("<b>", "").replace("</b>", ""),
        "address": it.get("roadAddress"),
        "coords": {
            "x": it.get("mapx"),
            "y": it.get("mapy"),
        },
        "raw": it,
    }
