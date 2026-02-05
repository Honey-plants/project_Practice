import re

BLOCK_WORDS = ("승인", "거래", "주문", "영수증", "전표", "번호", "No", "NO", "ID")

# 번호: 202600200003448 같은 거래/전표 번호 컷
TRANSACTION_NO_REGEX = re.compile(r'번호\s*:\s*\d{8,}')

PHONE_REGEX = re.compile(
    r'(?<!\d)'                 # 앞이 숫자가 아니어야 함
    r'(0\d{1,2})'              # 지역번호 / 010 / 011 ...
    r'[\)\-\s]*'
    r'(\d{3,4})'
    r'[\-\s]*'
    r'(\d{4})'
    r'(?!\d)'                  # 뒤가 숫자가 아니어야 함
)

def extract_phone(lines):
    best = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 1) 번호: + 긴 숫자는 무조건 스킵 (거래/전표 번호)
        if TRANSACTION_NO_REGEX.search(line):
            continue

        # 2) 거래/승인/전표 관련 키워드 있으면 스킵
        #    단, TEL/전화/연락처가 있으면 예외 허용
        if any(w in line for w in BLOCK_WORDS):
            if not any(k in line.lower() for k in ("tel", "전화", "연락처", "phone")):
                continue

        m = PHONE_REGEX.search(line)
        if not m:
            continue

        phone = "".join(m.groups())

        # 3) 길이 체크
        # 02: 9~10자리 / 그 외: 10~11자리
        if phone.startswith("02"):
            if len(phone) not in (9, 10):
                continue
        else:
            if len(phone) not in (10, 11):
                continue

        # 4) 명백한 쓰레기 패턴 제거
        if "0000" in phone or phone.endswith("0000"):
            continue

        best = phone
        break

    return best
