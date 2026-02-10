import re
import requests as http_requests
from typing import Optional, Dict, Any

def _extract_city(address: Optional[str]) -> Optional[str]:
    if not address:
        return None
    parts = address.strip().split()
    return parts[0] if parts else None


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def _clean_query(q: str) -> str:
    q = (q or "").strip()
    q = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", q)  # zero-width 제거
    q = re.sub(r"\s{2,}", " ", q)
    return q


def find_store_by_query(
    query: str,
    *,
    client_id: str,
    client_secret: str,
) -> Optional[Dict[str, Any]]:
    query = _clean_query(query)
    if not query:
        return None

    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }

    def _call(sort: str) -> Optional[dict]:
        params = {"query": query, "display": 5, "sort": sort}
        r = http_requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except Exception:
            return None

    # 1차: random(기본)
    js = _call("random")
    if not js:
        return None
    items = js.get("items") or []

    # 이상 케이스 대응: total은 있는데 items가 비어있음 → sort 바꿔서 재시도
    if not items and (js.get("total") or 0) > 0:
        js2 = _call("comment")
        if js2:
            items = js2.get("items") or []

    if not items:
        return None

    it = items[0]
    address = it.get("roadAddress") or it.get("address")
    city = _extract_city(address)

    return {
        "name_ko": _strip_html(it.get("title") or ""),
        "address": it.get("roadAddress"),
        "city": city,
        "coords": {"x": it.get("mapx"), "y": it.get("mapy")},
        "raw": it,
    }
