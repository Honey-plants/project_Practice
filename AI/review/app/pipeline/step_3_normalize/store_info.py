import re

# 지역명 키워드와 지역번호 매핑
AREA_CODE_MAP = {
    "서울": "02",
    "경기": "031",
    "인천": "032",
    "경북": "054",
    "경상북도": "054",
    "부산": "051",
    "대구": "053",
    "포항": "054"  # 포항은 경북이므로 054
}

#지역번호 없을때 텍스트값으로 번호찾아주기 (default=서울(02))
def detect_area_code(lines):
    # 기본값 설정
    detected_code = "02"

    for line in lines:
        # line이 아무리 길어도 '경상북도'가 포함되어 있는지 확인
        for city, code in AREA_CODE_MAP.items():
            if city in line:
                print(f"지역 키워드 발견: '{city}' (문장: {line[:30]}...) -> 지역번호 {code} 적용")
                return code

    return detected_code

#전화번호 추출
def extract_phone(lines):
    PHONE_REGEX = re.compile(
        r'(0\d{1,2})[-\s]?(\d{3,4})[-\s]?(\d{4})'
    )

    for line in lines:
        match = PHONE_REGEX.search(line)
        if match:
            phone = "".join(match.groups())
            return phone

    return None