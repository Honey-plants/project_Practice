# AI/review/app/pipeline/step_4_enrich_data/store_name_candidates.py
from __future__ import annotations
import re
from typing import List

BANNED = [
    "영수증","매장명","사업자","대표자","TEL","전화","주문","고객","합계","부가세","과세",
    "금액","단가","수량","상품명","카드","승인","결제","매출","거래","현금","봉사료"
]

def extract_store_name_candidates(lines: List[str], *, top_k: int = 10, max_candidates: int = 5) -> List[str]:
    """
    영수증 상단부에서 매장명 후보 뽑기 (간단 휴리스틱)
    - 상단 top_k 줄만 봄
    - [매장명] 같이 라벨 있으면 그 다음 텍스트를 우선
    """
    head = [l.strip() for l in lines[:top_k] if l and l.strip()]
    cands: List[str] = []

    # 1) 라벨 기반: [매장명]XXX / 매장명: XXX
    label_re = re.compile(r"(?:^\[?매장명\]?\s*[:\]]?\s*)(.+)$")
    for l in head:
        m = label_re.search(l)
        if m:
            name = m.group(1).strip()
            name = re.sub(r"[\[\]<>/]", "", name)
            name = re.sub(r"\s{2,}", " ", name).strip()
            if name and len(name) >= 2:
                cands.append(name)

    # 2) 일반 후보: 한글/영문 위주 + 너무 긴 줄 제거 + 금칙어 포함 제거
    for l in head:
        if any(b in l for b in BANNED):
            continue
        # 숫자/기호가 너무 많으면 제외
        only = re.sub(r"[^가-힣A-Za-z\s]", "", l).strip()
        only = re.sub(r"\s{2,}", " ", only)
        if 2 <= len(only) <= 20:
            cands.append(only)

    # dedupe preserve order
    out: List[str] = []
    for x in cands:
        if x not in out:
            out.append(x)
        if len(out) >= max_candidates:
            break
    return out
