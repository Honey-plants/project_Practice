from __future__ import annotations
import re
from typing import List

BANNED = [
    "영수증","잔액", "공급", "매장명","사업자","대표자","대표","TEL","전화","주문","고객","합계","부가세","과세",
    "금액","교환권","단가","수량","상품명","카드","승인","결제","매출","거래","현금","봉사료",
    "결제방법","카드번호","할부","승인번호","승인일시","가맹점번호","사업자등록번호","대표번호","주소"
]

MENU_SECTION_TRIGGERS = ["상품명", "수량", "단가", "금액", "품명", "메뉴"]

def extract_store_name_candidates(lines: List[str], *, top_k: int = 10, max_candidates: int = 5) -> List[str]:

    # 방어: None / 빈 리스트 대응
    if not lines:
        return []

    # 0) 전처리: 빈줄 제거 + strip
    cleaned = [l.strip() for l in lines if l and l.strip()]

    # 1) 기본 head
    head = cleaned[:top_k]
    cands: List[str] = []

    # --- helper ---
    def _clean_name(name: str) -> str:
        name = (name or "").strip()
        # HTML/괄호/특수 제거(너무 공격적이면 줄여도 됨)
        name = re.sub(r"<[^>]+>", " ", name)         # <b> 제거 등
        name = re.sub(r"\([^)]*\)", " ", name)       # (주) 같은 괄호 제거
        name = re.sub(r"[\[\]<>/]", " ", name)
        name = re.sub(r"\s{2,}", " ", name).strip()
        return name

    def _is_valid_candidate(s: str) -> bool:
        if not s or len(s) < 2 or len(s) > 30:
            return False
        # 금칙어가 포함되면 제외
        if any(b in s for b in BANNED):
            return False
        # 숫자 비율이 너무 높으면 제외
        digits = sum(ch.isdigit() for ch in s)
        if digits >= max(3, len(s) // 2):
            return False
        return True

    # 2) 라벨 기반 (상단 head에서)
    #   - [매장명] xxx / 매장명: xxx / 상호: xxx / 상호 xxx
    label_re = re.compile(
        r"^\s*(?:\[?\s*(매장명|상호)\s*\]?\s*[:\]]?\s*)(.+)\s*$"
    )

    for l in head:
        m = label_re.search(l)
        if m:
            name = _clean_name(m.group(2))
            if _is_valid_candidate(name):
                cands.append(name)

    # 3) "상호" 라벨이 단독으로 찍히는 영수증 대응:
    #    예) "상호" 다음 줄에 "OOO"
    #    이 패턴은 상단 밖에도 자주 있어서 cleaned 전체에서 앞쪽 60줄 정도만 탐색
    scan_n = min(len(cleaned), 60)
    for i in range(scan_n - 1):
        if cleaned[i] in ("상호", "[상호]", "매장명", "[매장명]"):
            name = _clean_name(cleaned[i + 1])
            if _is_valid_candidate(name):
                cands.append(name)

    # 4) 메뉴 섹션 트리거 전까지의 “이름스럽게 생긴” 짧은 한글/영문 라인 후보
    #    (상단에서만) - 숫자/기호 제거 후 길이 제한
    for l in head:
        # 메뉴 섹션 시작 느낌이면 중단
        if any(t in l for t in MENU_SECTION_TRIGGERS):
            break
        if any(b in l for b in BANNED):
            continue

        only = re.sub(r"[^가-힣A-Za-z\s]", "", l).strip()
        only = re.sub(r"\s{2,}", " ", only)

        # 너무 흔한 텍스트(예: place.naver.com) 제거
        if "NAVER" in only.upper() or "PLACE" in only.upper():
            continue

        if 2 <= len(only) <= 25 and _is_valid_candidate(only):
            cands.append(only)

    # 5) dedupe preserve order + max_candidates
    out: List[str] = []
    for x in cands:
        if x not in out:
            out.append(x)
        if len(out) >= max_candidates:
            break

    print("out", out)
    return out
