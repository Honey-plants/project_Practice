# ai/journal/food_journal_prompt.py
import json
from io import BytesIO
from PIL import Image
from typing import Any, Dict, List
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API")

client = genai.Client(
    api_key=API_KEY
)

def naver_xy_to_latlon(x: str, y: str):
    """
    Naver coords:
      x = lon * 1e7
      y = lat * 1e7
    """
    lon = float(x) / 1e7
    lat = float(y) / 1e7
    return lat, lon


# =========================
# 2) 입력 데이터 (네가 준 그대로)
# =========================
PLACES_RAW = [
    {
        "coords": {"x": "1277400846", "y": "378573820"},
        "menu_name": [
            "대원당맘모스구로",
            "버터크림빵",
            "감자법버빵",
            "팔빙수",
            "자몽에이드",
            "진동별",
        ],
        # 우리가 명시적으로 영어 지정 (AI에게 맡기지 않음)
        "place_en": "Chuncheon (Gangwon-do)",
    },
    {
        "coords": {"x": "1273548632", "y": "376256774"},
        "menu_name": [
            "닭갈비",
            "소금",
            "전병",
            "후레쉬",
            "지평막걸리",
            "된장찌개공깃밥",
            "비빔막국수",
            "물막국수",
        ],
        "place_en": "Chuncheon (Gangwon-do)",
    },
    {
        "coords": {"x": "1271129462", "y": "373218802"},
        "menu_name": [
            "라지냐",
            "쉬림프알리오",
            "코카콜라",
        ],
        "place_en": "Seoul",
    },
]


# =========================
# 3) 장소 요약 생성
# =========================
def build_place_summaries(places_raw: List[Dict]):
    summaries = []
    latlons = []

    for i, p in enumerate(places_raw, start=1):
        lat, lon = naver_xy_to_latlon(p["coords"]["x"], p["coords"]["y"])
        latlons.append((lat, lon))

        menus = ", ".join(p["menu_name"][:4])  # 너무 길면 앞 4개만
        summaries.append(
            f"{i}) {p['place_en']} — {menus}"
        )

    return summaries, latlons


# =========================
# 4) Gemini용 지도 오버레이 프롬프트
# =========================
def build_map_overlay_prompt(
    place_summaries: List[str],
    title: str = "MY KOREA FOOD MAP"
) -> str:

    places_text = "\n".join(place_summaries)

    return f"""
Edit the provided map image.

STRICT RULES (VERY IMPORTANT):
- Do NOT change the base map image.
- Do NOT translate or replace any Korean labels on the map.
- Do NOT move or resize the map.
- Do NOT move the existing pin markers.

GOAL:
Create a clean SNS-style food travel journal overlay.

ADD:
1) A title at the top-left:
   "{title}"

2) A semi-transparent white outer overlay panel
   placed on the right side or in an empty ocean area.
   - Rounded corners
   - Subtle shadow
   - Minimal, modern style

3) Inside the panel, list the visited places EXACTLY as written:
{places_text}

4) A small footer line:
   "Pinned from receipt coordinates • Korea Food Journal"

STYLE:
- Clean
- Readable
- Travel journal vibe
- No cartoons, no extra icons
- Do not clutter the image

OUTPUT:
- One final SNS-ready image.
"""



def generate_journal(journal_prompt: str, image_path: str):
    """
    Gemini IMAGE EDIT:
    - image_path: base map image (from KakaoMap)
    - journal_prompt: overlay instructions
    """

    with open(image_path, "rb") as f:
        base_image_bytes = f.read()

    img_part = types.Part(
        inline_data=types.Blob(
            mime_type="image/png",
            data=base_image_bytes
        )
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[img_part, journal_prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    )

    if not response.candidates or not response.candidates[0].content:
        print("⚠️ Gemini failed to generate image")
        return None

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

    return None


if __name__ == "__main__":
    summaries, latlons = build_place_summaries(PLACES_RAW)

    print("=== Converted lat/lon (for map pins) ===")
    for i, (lat, lon) in enumerate(latlons, 1):
        print(f"{i}: lat={lat:.6f}, lon={lon:.6f}")

    prompt = build_map_overlay_prompt(summaries, latlons)


    image_bytes = generate_journal(
        journal_prompt=prompt,
        image_path="kakao_korea_full.png"  # ← KakaoMap으로 만든 지도
    )

    if image_bytes is None:
        raise RuntimeError("Gemini image generation failed")

    img = Image.open(BytesIO(image_bytes))
    img.save("food_journal_map_final.png")
    print("✅ saved: food_journal_map_final.png")