import requests as http_requests
from typing import Optional, Dict, Any


def _extract_city(address: Optional[str]) -> Optional[str]:
    """
    roadAddress에서 첫 지역명 추출
    예:
    - '경기 용인시 기흥구 죽전로 43번길 19' → '경기'
    - '서울 강남구 테헤란로 123' → '서울'
    """
    if not address:
        return None

    parts = address.strip().split()
    return parts[0] if parts else None

def find_store_by_phone(
    phone: str,
    *,
    client_id: str,
    client_secret: str,
) -> Optional[Dict[str, Any]]:

    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": phone,
        "display": 5,  # ✅ 1 말고 5로 늘려서 확인
    }

    r = http_requests.get(url, headers=headers, params=params, timeout=10)

    # ✅ 디버그
    try:
        js = r.json()
    except Exception:
        print("[naver] non-json response:", r.status_code, r.text[:200])
        return None

    if r.status_code != 200:
        print("[naver] error:", r.status_code, js)
        return None

    items = js.get("items") or []
    print(f"[naver] query={phone} total={js.get('total')} items={len(items)}")

    if not items:
        return None

    # 일단 전부 제목 찍어보기
    for i, it in enumerate(items[:5]):
        title = (it.get("title") or "").replace("<b>", "").replace("</b>", "")
        print(f"[naver] item{i} title={title} addr={it.get('roadAddress')} tel={it.get('telephone')}")

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