from __future__ import annotations
import re
from typing import List

PRICE_RE = re.compile(r"\d{1,3}(?:,\d{3})+|\d{4,}")

START_KEYWORDS = ["메뉴", "단가", "금액", "수량", "품명"]
STOP_KEYWORDS = ["부가세", "합계", "결제", "신용", "카드", "총액", "판매", "금 액"]

# 메뉴로 절대 들어가면 안 되는 단어
BANNED_MENU = set(START_KEYWORDS + STOP_KEYWORDS)


def extract_menu_items(lines: List[str]) -> List[str]:
    menu_items: List[str] = []
    started = False  # ✅ START는 한 번만

    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        # 1️⃣ START (1회)
        if not started and any(k in line for k in START_KEYWORDS):
            started = True
            continue

        if not started:
            continue

        # 2️⃣ STOP 나오면 즉시 종료
        if any(k in line for k in STOP_KEYWORDS):
            break

        # START 키워드 줄 제거 (← 핵심 추가)
        if any(k in line for k in START_KEYWORDS):
            continue

        # 3️⃣ 가격 포함된 줄
        if PRICE_RE.search(line):
            name = re.sub(PRICE_RE, "", line)
            name = re.sub(r"\d+", "", name)
            name = re.sub(r"[^가-힣 ]", "", name).strip()

            if name and name not in BANNED_MENU and re.search(r"[가-힣]{2,}", name):
                menu_items.append(name)
                continue

            # 이전 줄 fallback
            if i > 0:
                prev = re.sub(r"[^가-힣 ]", "", lines[i - 1]).strip()
                if prev and prev not in BANNED_MENU and re.search(r"[가-힣]{2,}", prev):
                    menu_items.append(prev)
            continue

        # 4️⃣ 가격 없는 줄 (메뉴 후보)
        name_tokens = re.sub(r"[^가-힣 ]", "", line).strip()
        if name_tokens and name_tokens not in BANNED_MENU and re.search(r"[가-힣]{2,}", name_tokens):
            menu_items.append(name_tokens)

    # ✅ 중복 제거 (순서 유지)
    out: List[str] = []
    for m in menu_items:
        if m not in out:
            out.append(m)

    return out
