import requests as http_requests
from fastapi import Request
import re



def normalize_ocr_lines(result_item):
    """
    Convert PaddleOCR v3.x output to a consistent format: (bbox, text, score)
    """
    rec_texts = result_item['rec_texts']
    rec_scores = result_item['rec_scores']
    rec_polys = result_item['rec_polys']

    tokens = []
    for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
        x_coords = poly[:, 0]
        y_coords = poly[:, 1]
        tokens.append({
            'text': text,
            'score': score,
            'x_min': int(x_coords.min()),
            'x_max': int(x_coords.max()),
            'y_min': int(y_coords.min()),
            'y_max': int(y_coords.max()),
        })
    return tokens



# =======================================
# TOKEN 라인별로 조인해주기
# =======================================
def join_split_tokens(tokens, y_threshold=15):
    # 1. Y좌표 순으로 정렬
    tokens.sort(key=lambda x: x['y_min'])

    lines = []
    if not tokens: return lines

    current_line = [tokens[0]]

    for i in range(1, len(tokens)):
        # 이전 토큰과 Y좌표 차이가 threshold(예: 10px) 이내면 같은 줄로 간주
        if abs(tokens[i]['y_min'] - current_line[-1]['y_min']) < y_threshold:
            current_line.append(tokens[i])
        else:
            # 줄이 바뀌면 현재까지 모인 토큰들을 합쳐서 저장
            current_line.sort(key=lambda x: x['x_min'])  # X좌표 순(왼쪽->오른쪽) 정렬
            lines.append(" ".join([t['text'] for t in current_line]))
            current_line = [tokens[i]]

    # 마지막 줄 처리
    current_line.sort(key=lambda x: x['x_min'])
    lines.append(" ".join([t['text'] for t in current_line]))

    # with open("lines_joined_10.json", "w", encoding="utf-8") as f:
    #     json.dump(lines, f, ensure_ascii=False, indent=2)
    return lines


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

#전화번호로 사업자 정보 검색(가게명, 주소, 번호, 위치)
def find_location(query):
    client_id = "45476rdzYavZqCFMWGI5"
    client_secret = "PDPZB2w7RS"
    # 지역 검색 API 엔드포인트
    url = "https://openapi.naver.com/v1/search/local.json"
    params = {
        "query": query,  # 전화번호나 상호명
        "display": 1  # 가장 정확한 1건만 출력
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }


    response = http_requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        items = response.json().get('items')
        if items:
            place = items[0]
            return place
        else:
            print("결과를 찾을 수 없습니다.")
    else:
        print(f"Error: {response.status_code}")

# ==============================================
# 메뉴명 추출
# ==============================================

PRICE_RE = re.compile(r"\d{1,3}(,\d{3})+")

def extract_menu_items(lines):
    menu_items = []

    START_KEYWORDS = ["메뉴", "단가", "금액", "수량", "품명"]
    STOP_KEYWORDS = ["부가세", "합계", "결제", "신용", "카드", "총액"]

    in_menu_section = False

    for i, line in enumerate(lines):
        line = line.strip()

        # 1️Start condition
        if not in_menu_section and any(k in line for k in START_KEYWORDS):
            in_menu_section = True
            continue

        if not in_menu_section:
            continue

        # 2️Stop condition
        if any(k in line for k in STOP_KEYWORDS):
            break

        # 메타 제거
        if line.startswith("[") and "]" in line:
            continue

        # START 키워드 줄 제거 (← 핵심 추가)
        if any(k in line for k in START_KEYWORDS):
            continue

        # 가격 줄
        if PRICE_RE.search(line):
            name = re.sub(PRICE_RE, "", line)
            name = re.sub(r"\d+", "", name)
            name = re.sub(r"[^가-힣 ]", "", name).strip()

            if re.search(r"[가-힣]{2,}", name):
                menu_items.append(name)
                continue

            if i > 0:
                prev = lines[i - 1]
                prev = re.sub(r"[^가-힣 ]", "", prev).strip()
                if re.search(r"[가-힣]{2,}", prev):
                    menu_items.append(prev)
            continue

        # 🔑 가격 없는 줄 (메뉴 후보)
        name_tokens = re.sub(r"[^가-힣 ]", "", line).strip()
        if re.search(r"[가-힣]{2,}", name_tokens):
            menu_items.append(name_tokens)

    # 중복 제거
    result = []
    for m in menu_items:
        if m not in result:
            result.append(m)

    return result


def is_menu_token(token_text, menu_lines):
    return any(token_text in line for line in menu_lines)

def build_receipt_json(ocr_lines):
    """
    OCR raw result (result[0]) → structured receipt JSON
    No file I/O, no side effects
    """

    # 1. Normalize OCR tokens
    tokens = normalize_ocr_lines(ocr_lines)
    # 2. Merge tokens into readable lines
    lines = join_split_tokens(tokens)
    # 3. Extract phone number
    phone = extract_phone(lines)

    # 4. Extract menu items
    menu_ko = extract_menu_items(lines)

    # 5. Find store info (optional, via phone)
    store_info = None
    if phone:
        store_info = find_location(phone)

    # 6. Build final receipt JSON
    if store_info:
        receipt_json = {
            "store_name": store_info["title"]
                .replace("<b>", "")
                .replace("</b>", ""),
            "address": store_info.get("roadAddress"),
            "city": store_info.get("roadAddress", "").split(" ")[0],
            "phone": phone,
            "coords": {
                "x": store_info.get("mapx"),
                "y": store_info.get("mapy"),
            },
            "menu_name": menu_ko,
        }
    else:
        receipt_json = {
            "store_name": None,
            "address": None,
            "city": None,
            "phone": phone,
            "coords": None,
            "menu_name": menu_ko,
        }

    return receipt_json
