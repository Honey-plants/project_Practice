# map_overlay_from_calib_json.py
# ------------------------------------------------------------
# Uses:
# - kakao_map_calibration.json (saved earlier)
# - base_map.png (your decorated map image, MUST match calibration size)
#
# Outputs:
# - pinned_map.png (pins drawn by Pillow)
# - final_map_overlay.png (Gemini adds travel-log overlay, English-only)
#
# Install:
#   pip install pillow python-dotenv google-genai
#
# .env:
#   GOOGLE_API=YOUR_GEMINI_API_KEY
#
# Run:
#   python map_overlay_from_calib_json.py
# ------------------------------------------------------------

import os
import json
import math
from io import BytesIO
from typing import Tuple, List, Dict

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from google import genai
from google.genai import types


# =========================
# FILE PATHS (EDIT)
# =========================
CALIB_JSON_PATH = "kakao_map_calibration.json"  # created from your calibration step
BASE_MAP_PATH = "base_map1.png"                  # your decorated map (same size as calibration)
OUT_PINNED = "pinned_map.png"
OUT_FINAL = "final_map_overlay.png"


# =========================
# GEMINI CONFIG
# =========================
GEMINI_MODEL = "gemini-2.5-flash-image"


# =========================
# NAVER COORDS (x=lon*1e7, y=lat*1e7) + MENUS
# EVERYTHING MUST BE IN ENGLISH -> we provide EN translations here.
# =========================
PLACES: List[Dict] = [
    {
        "label": "1",
        "coords": {"x": "1277400846", "y": "378573820"},
        "place_en": "Chuncheon, Gangwon-do",
        "menu_en": [
            "Daewondang Mammoth (Guro) (store name)",
            "Butter Cream Bread",
            "Potato Mash Bread (approx.)",
            "Red Bean Shaved Ice (Patbingsu)",
            "Grapefruit Ade",
            "Jindong Byeol (romanized item name)",
        ],
        # ONE photo per point: set a local image path if you have it.
        # If missing, the script generates a placeholder image automatically.
        "food_photo_path": "",  # e.g. "photos/patbingsu.jpg"
        "photo_title_en": "Red Bean Shaved Ice (Patbingsu)",
    },
    {
        "label": "2",
        "coords": {"x": "1273548632", "y": "376256774"},
        "place_en": "Chuncheon, Gangwon-do",
        "menu_en": [
            "Spicy Stir-fried Chicken (Dak-galbi)",
            "Salt",
            "Jeonbyeong (Korean rolled pancake snack)",
            "Fresh Soju (approx.)",
            "Jipyeong Makgeolli",
            "Soybean Paste Stew + Rice",
            "Spicy Mixed Buckwheat Noodles (Bibim Makguksu)",
            "Cold Buckwheat Noodle Soup (Mul Makguksu)",
        ],
        "food_photo_path": "",  # e.g. "photos/dakgalbi.jpg"
        "photo_title_en": "Spicy Stir-fried Chicken (Dak-galbi)",
    },
    {
        "label": "3",
        "coords": {"x": "1271129462", "y": "373218802"},
        "place_en": "Seoul",
        "menu_en": [
            "Lasagna",
            "Shrimp Aglio e Olio",
            "Coca-Cola",
        ],
        "food_photo_path": "",  # e.g. "photos/aglio.jpg"
        "photo_title_en": "Shrimp Aglio e Olio",
    },
]


# =========================
# COORD + PROJECTION
# =========================
def naver_xy_to_latlon(x: str, y: str) -> Tuple[float, float]:
    lon = float(x) / 1e7
    lat = float(y) / 1e7
    return lat, lon


def mercator_norm_xy(lat: float, lon: float) -> Tuple[float, float]:
    x = (lon + 180.0) / 360.0
    siny = math.sin(math.radians(lat))
    siny = min(max(siny, -0.9999), 0.9999)
    y = 0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)
    return x, y


def latlon_to_image_px_calibrated(
    lat: float,
    lon: float,
    center_lat: float,
    center_lon: float,
    scale: float,
    img_w: int,
    img_h: int,
) -> Tuple[int, int]:
    cxn, cyn = mercator_norm_xy(center_lat, center_lon)
    xn, yn = mercator_norm_xy(lat, lon)
    px = (img_w / 2.0) + scale * (xn - cxn)
    py = (img_h / 2.0) + scale * (yn - cyn)
    return int(round(px)), int(round(py))


# =========================
# CALIB LOAD + VALIDATE
# =========================
def load_and_validate_calibration(base_w: int, base_h: int) -> Dict:
    with open(CALIB_JSON_PATH, "r", encoding="utf-8") as f:
        calib = json.load(f)

    if int(calib["width"]) != base_w or int(calib["height"]) != base_h:
        raise RuntimeError(
            f"[CALIB ERROR] Base image size {base_w}x{base_h} does not match calibration "
            f"{calib['width']}x{calib['height']}. "
            f"Your base_map.png must be the SAME frame/size as the calibrated map."
        )

    return calib


# =========================
# DRAW PINS
# =========================
def load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in ["arialbd.ttf", "Arial Bold.ttf", "Arial-Bold.ttf", "arial.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_number_pin(draw: ImageDraw.ImageDraw, x: int, y: int, text: str):
    r = 14
    draw.ellipse(
        (x - r, y - r, x + r, y + r),
        fill=(0, 122, 255, 255),
        outline=(255, 255, 255, 255),
        width=3,
    )
    font = load_font(14)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2 - 1), text, font=font, fill=(255, 255, 255, 255))


def make_pinned_map() -> str:
    base = Image.open(BASE_MAP_PATH).convert("RGBA")
    bw, bh = base.size

    calib = load_and_validate_calibration(bw, bh)
    center_lat = float(calib["center_lat"])
    center_lon = float(calib["center_lon"])
    scale = float(calib["scale"])

    draw = ImageDraw.Draw(base)

    for p in PLACES:
        lat, lon = naver_xy_to_latlon(p["coords"]["x"], p["coords"]["y"])
        x, y = latlon_to_image_px_calibrated(lat, lon, center_lat, center_lon, scale, bw, bh)
        inside = 0 <= x < bw and 0 <= y < bh
        print(f"[pin] {p['label']} {p['place_en']} -> px=({x},{y}) inside={inside}")
        draw_number_pin(draw, x, y, p["label"])

    base.save(OUT_PINNED)
    print(f"✅ saved pinned map: {OUT_PINNED}")
    return OUT_PINNED


# =========================
# FOOD PHOTO (one per point)
# If you don't have a photo, we generate a clean placeholder image.
# =========================
def generate_placeholder_food_image(title: str, out_path: str, size=(420, 320)):
    img = Image.new("RGBA", size, (245, 245, 245, 255))
    d = ImageDraw.Draw(img)

    # border
    d.rounded_rectangle((12, 12, size[0] - 12, size[1] - 12), radius=24, outline=(30, 30, 30, 255), width=3)

    # title
    font = load_font(22)
    text = title.strip()
    # simple wrap
    words = text.split()
    lines = []
    line = []
    for w in words:
        test = " ".join(line + [w])
        bbox = d.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > (size[0] - 60) and line:
            lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))

    y = 120
    for ln in lines[:3]:
        bbox = d.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        d.text(((size[0] - tw) / 2, y), ln, font=font, fill=(20, 20, 20, 255))
        y += 34

    # small subtitle
    font2 = load_font(16)
    subtitle = "Food photo placeholder"
    bbox = d.textbbox((0, 0), subtitle, font=font2)
    tw = bbox[2] - bbox[0]
    d.text(((size[0] - tw) / 2, size[1] - 70), subtitle, font=font2, fill=(80, 80, 80, 255))

    img.save(out_path)
    return out_path


def get_food_image_paths() -> List[str]:
    paths = []
    for i, p in enumerate(PLACES, start=1):
        path = (p.get("food_photo_path") or "").strip()
        if path and os.path.exists(path):
            paths.append(path)
        else:
            # generate placeholder
            ph_path = f"_food_placeholder_{i}.png"
            generate_placeholder_food_image(p["photo_title_en"], ph_path)
            paths.append(ph_path)
    return paths


# =========================
# GEMINI OVERLAY PROMPT (ENGLISH ONLY)
# =========================
def build_overlay_prompt() -> str:
    stops = []
    for p in PLACES:
        # pick 3 representative menu items
        menus = ", ".join(p["menu_en"][:3])
        stops.append(f"STOP {p['label']}: {p['place_en']} | Menus: {menus}")

    stops_text = "\n".join(stops)

    return (
        "Transform the provided pinned map into a VINTAGE TRAVEL ROADMAP POSTER.\n"
        "EVERYTHING MUST BE IN ENGLISH ONLY.\n\n"

        "ABSOLUTE RULES:\n"
        "- Keep the exact same image size and aspect ratio as the input.\n"
        "- Do NOT crop, resize, rotate, or extend the canvas.\n"
        "- Do NOT remove the coastline/outline of Korea.\n"
        "- The existing numbered pins must remain visible and readable (1, 2, 3).\n\n"

        "STYLE:\n"
        "- Vintage travel poster / parchment paper feel.\n"
        "- Minimal but playful travel infographic.\n"
        "- Warm paper background, simple line art.\n"
        "- NO modern 'right-side UI panel' layout.\n\n"

        "LAYOUT GOAL (VERY IMPORTANT):\n"
        "- Make it look like a ROAD TRIP MAP poster.\n"
        "- Add a red dashed route line connecting Stop 1 -> Stop 2 -> Stop 3.\n"
        "- Add small arrowheads on the dashed route showing direction.\n"
        "- Add 3 'photo cards' (one per stop) placed near the route.\n"
        "- Each photo card uses the corresponding food photo input.\n"
        "- Each card has a short English caption and 2–3 menu names.\n\n"

        "TEXT CONTENT (use only this data, do not invent items):\n"
        f"{stops_text}\n\n"

        "POSTER TEXT:\n"
        "- Title at top: 'KOREA FOOD TRIP MAP'\n"
        "- Subtitle under title: 'A Receipt-Pinned Food Journey'\n"
        "- Add a circular stamp graphic (English): 'KOREA ADVENTURE'\n"
        "- Small footer: 'Pinned from receipt coordinates'\n\n"

        "CARD FORMAT (for each stop):\n"
        "- 'STOP X — <Place>'\n"
        "- 2–3 menu items (English)\n"
        "- ONE short diary sentence (tourist tone), based on menus only.\n\n"

        "OUTPUT:\n"
        "- One final poster-style image.\n"
    )


def gemini_add_overlay(map_image_path: str, food_image_paths: List[str]) -> bytes:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API in .env")

    client = genai.Client(api_key=api_key)

    def img_part(path: str) -> types.Part:
        with open(path, "rb") as f:
            b = f.read()
        return types.Part(inline_data=types.Blob(mime_type="image/png", data=b))

    prompt = build_overlay_prompt()

    parts = [img_part(map_image_path)]
    for p in food_image_paths:
        parts.append(img_part(p))
    parts.append(prompt)

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=parts,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    if not resp.candidates or not resp.candidates[0].content:
        raise RuntimeError("Gemini returned no image (blocked or failed).")

    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

    raise RuntimeError("Gemini response had no inline image data.")


def main():
    pinned_map_path = make_pinned_map()
    food_paths = get_food_image_paths()

    print("[info] food photos used:")
    for i, p in enumerate(food_paths, start=1):
        print(f"  STOP {i}: {p}")

    out_bytes = gemini_add_overlay(pinned_map_path, food_paths)

    img = Image.open(BytesIO(out_bytes)).convert("RGBA")
    img.save(OUT_FINAL)
    print(f"✅ saved final overlay image: {OUT_FINAL}")


if __name__ == "__main__":
    main()
