from __future__ import annotations
import re
from typing import List

PRICE_RE = re.compile(r"\d{1,3}(?:,\d{3})+|\d{4,}")

START_KEYWORDS = ["메뉴", "단가", "금액", "수량", "품명", "리뷰"]
STOP_KEYWORDS = ["부가세", "합계", "결제", "신용", "카드", "총액", "판매", "금 액", "현금", "공급"]

BANNED_MENU = set(START_KEYWORDS + STOP_KEYWORDS)

#  "몇개" 제거용
REMOVE_GAE_RE = re.compile(r"\b개\b")          # 토큰 '개'
REMOVE_QTY_GAE_RE = re.compile(r"\d+\s*개")    # '1개', '2 개' 등

CUT_TAIL_KEYWORDS = [
    "리뷰", "영수증", "작성", "작성시", "이벤트", "쿠폰", "증정", "할인", "적립", "서비스",
]

def _clean_menu_name(s: str) -> str:
    # 숫자+개 먼저 제거
    s = REMOVE_QTY_GAE_RE.sub("", s)
    s = REMOVE_GAE_RE.sub("", s)

    # 공백 정리
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"개$", "", s).strip()

    # "리뷰/영수증/작성시..." 같은 문구가 나오면 그 지점부터 잘라버리기
    for kw in CUT_TAIL_KEYWORDS:
        idx = s.find(kw)
        if idx != -1:
            s = s[:idx].strip()
            break

    # 혹시 잘라서 너무 짧아진 경우 방어
    return s.strip()


def extract_menu_items(lines: List[str]) -> List[str]:
    menu_items: List[str] = []
    started = False

    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        # START 1회
        if not started and any(k in line for k in START_KEYWORDS):
            started = True
            continue
        if not started:
            continue

        # STOP
        if any(k in line for k in STOP_KEYWORDS):
            break

        # START 키워드 줄 제거
        if any(k in line for k in START_KEYWORDS):
            continue

        # 가격 포함된 줄
        if PRICE_RE.search(line):
            name = re.sub(PRICE_RE, "", line)
            name = re.sub(r"\d+", "", name)
            name = re.sub(r"[^가-힣 ]", "", name).strip()

            #  여기서 "개" 제거
            name = _clean_menu_name(name)

            if name and name not in BANNED_MENU and re.search(r"[가-힣]{2,}", name):
                menu_items.append(name)
                continue

            # 이전 줄 fallback
            if i > 0:
                prev = re.sub(r"[^가-힣 ]", "", lines[i - 1]).strip()
                prev = _clean_menu_name(prev)  #  여기서도 "개" 제거
                if prev and prev not in BANNED_MENU and re.search(r"[가-힣]{2,}", prev):
                    menu_items.append(prev)
            continue

        # 가격 없는 줄 (메뉴 후보)
        name_tokens = re.sub(r"[^가-힣 ]", "", line).strip()
        name_tokens = _clean_menu_name(name_tokens)  #  여기서도 "개" 제거

        if name_tokens and name_tokens not in BANNED_MENU and re.search(r"[가-힣]{2,}", name_tokens):
            menu_items.append(name_tokens)

    # 중복 제거(순서 유지)
    out: List[str] = []
    for m in menu_items:
        if m not in out:
            out.append(m)

    return out
