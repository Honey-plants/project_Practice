from __future__ import annotations
from typing import Any, Dict, List


def build_map_poster_prompt_with_ref(
    payload: Dict[str, Any],
    *,
    canvas_w: int,
    canvas_h: int,
    map_left: int,
    map_top: int,
    map_w: int,
    map_h: int,
) -> str:
    member = payload.get("member", {})
    reviews: List[Dict[str, Any]] = payload.get("reviews", [])

    nickname = member.get("nickname", "Traveler")
    country = member.get("country", "Unknown")
    allergies = member.get("item_ids", [])
    allergy_text = ", ".join(allergies) if allergies else "none"

    eaten = []
    for r in reviews:
        eaten.append(r.get("review_title", "Food experience"))

    eaten_text = ", ".join(eaten) if eaten else "No meals recorded"
    print(eaten_text)
    map_box = f"x={map_left}..{map_left+map_w}, y={map_top}..{map_top+map_h}"

    #음식 이미지 사진 사이즈 고정시키기
    max_food_w = int(canvas_w * 0.06)   # 캔버스 가로의 12%
    max_food_h = int(canvas_h * 0.08)   # 캔버스 세로의 18% (원형/접시 고려)
    
    return f"""
CRITICAL:
You are EDITING the provided REFERENCE IMAGE.
The reference image already contains the map and location pins.

CANVAS:
- Output size MUST be exactly {canvas_w}x{canvas_h}.
- Do NOT crop, resize, or change aspect ratio.

LOCKED AREA (MAP AREA):
- The map rectangle is {map_box}.
- DO NOT modify ANY pixels inside the map rectangle.
- Do NOT add text, stickers, tape, shadows, texture, or food images inside that map rectangle.
- The map and pins must remain pixel-identical.

ALLOWED AREA (OUTSIDE MAP ONLY):
- Add a big title centered at top: "KFOOD roadmap with SafeEat"
- Subtitle: "By {nickname} from {country}"
- Add scrapbook accents around the outer background only (tape, stamps, doodles)

FOOD CUTOUTS (VERY IMPORTANT SIZE RULE):
- Food images must be SMALL sticker-like cutouts (secondary accents).
- Each food cutout must be no larger than {max_food_w}px wide AND {max_food_h}px tall.
- Each cutout should occupy at most 6% of the canvas width.
- Food cutouts must be clearly smaller than the map.
- If any food cutout looks big/dominant, the result is incorrect.

RECOMMENDED FOOD:
- Must respect allergies: avoid {allergy_text}
Food hints (based on reviews): {eaten_text}

PLACEMENT:
- Place JUST food image of eaten food cutouts RANDOMLY (not straight line but spread them out quite evenly throughout left side of the map) OUTSIDE the map area (LEFT side of the map)
- Place 3 recommended food cutouts + names OUTSIDE the map area (RIGHT side column).
- Keep consistent spacing; do not overlap elements.


STYLE:
- Minimal clean poster + light hanji texture (ONLY outside map area)
- English only
- No restaurant names, addresses, dates, social handles

RIGHT SIDE – RECOMMENDED KFOOD BOX (STRICT RULES):

- Create ONE rectangular recommendation box on the RIGHT side of the canvas.
- The box MUST have a visible border (hand-drawn or clean line style).
- The box must be clearly separated from the background.
- The box must be completely OUTSIDE the map rectangle.

BOX TITLE:
- Title text at the top of the box: "RECOMMENDED KFOOD"
- Title must be bold and clearly readable.
- DO NOT include allergy information in the title.
- DO NOT include parentheses, icons, or allergy tags in the title.

BOX CONTENT:
- Inside the box, place EXACTLY 3 Korean food items.
- Each item consists of:
  1) ONE small food cutout image
  2) ONE Korean food name in english (DO NOT JUST WRITE ENGLISH PRONOUNCIATION)
  - it must be fully translated eg 만두 should be written as dumpling NOT MANDU

FOOD IMAGE SIZE (IMPORTANT):
- Each food cutout must be small and sticker-like.
- Max size per food image:
  - Width ≤ 6% of canvas width
  - Height ≤ 8% of canvas height
- Food images must NOT dominate the box.
- Text must remain clearly readable next to or below each image.


OUTPUT:
Return ONE edited image.
""".strip()
