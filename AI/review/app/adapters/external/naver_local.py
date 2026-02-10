from __future__ import annotations
import requests as http_requests
from typing import Any, Dict, Optional

def find_location(query: str, *, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
    url = "https://openapi.naver.com/v1/search/local.json"
    params = {"query": query, "display": 1}
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}

    r = http_requests.get(url, headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        return None

    items = r.json().get("items") or []
    return items[0] if items else None
