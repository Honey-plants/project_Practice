import requests as http_requests
from typing import Optional, Dict, Any


def _extract_city(address: Optional[str]) -> Optional[str]:
    if not address:
        return None

    parts = address.strip().split()
    return parts[0] if parts else None

def format_korean_phone(phone: str) -> str:
    if phone.startswith("02") and len(phone) == 10:
        return f"02-{phone[2:6]}-{phone[6:]}"
    if phone.startswith("02") and len(phone) == 9:
        return f"02-{phone[2:5]}-{phone[5:]}"
    if phone.startswith("01"):
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    return phone

def find_store_by_query(
    query: str,
    *,
    client_id: str,
    client_secret: str,
) -> Optional[Dict[str, Any]]:
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {"query": query, "display": 5}

    r = http_requests.get(url, headers=headers, params=params, timeout=10)
    try:
        js = r.json()
    except Exception:
        return None
    if r.status_code != 200:
        return None

    items = js.get("items") or []
    if not items:
        return None

    it = items[0]
    address = it.get("roadAddress")
    city = _extract_city(address)

    return {
        "name_ko": (it.get("title") or "").replace("<b>", "").replace("</b>", ""),
        "address": it.get("roadAddress"),
        "city": city,
        "coords": {"x": it.get("mapx"), "y": it.get("mapy")},
        "raw": it,
    }