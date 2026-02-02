# pin_from_calib.py
import math
import json
from typing import Tuple, List, Dict
from PIL import Image, ImageDraw, ImageFont

CALIB_JSON_PATH = ".\AI\journal_assistant\pipeline\kakao_map_calibration.json"
BASE_IMAGE_PATH = ".\AI\journal_assistant\pipeline\map1.png"     # 핀 찍을 대상(꾸민 지도도 OK) - 반드시 동일한 frame/size
OUTPUT_PATH = "pinned_output.png"

# ✅ 여기만 바꾸면 됨: 매번 들어오는 Naver coords
PLACES_RAW: List[Dict] = [
    {"coords": {"x": "1277400846", "y": "378573820"}, "label": "1"},
    {"coords": {"x": "1273548632", "y": "376256774"}, "label": "2"},
    {"coords": {"x": "1271129462", "y": "373218802"}, "label": "3"},
]


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


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in ["arialbd.ttf", "Arial Bold.ttf", "Arial-Bold.ttf", "arial.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_number_pin(draw: ImageDraw.ImageDraw, x: int, y: int, text: str):
    r = 14
    draw.ellipse((x - r, y - r, x + r, y + r),
                 fill=(0, 122, 255, 255),
                 outline=(255, 255, 255, 255),
                 width=3)
    font = load_font(14)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2 - 1), text, font=font, fill=(255, 255, 255, 255))


def main():
    with open(CALIB_JSON_PATH, "r", encoding="utf-8") as f:
        calib = json.load(f)

    base = Image.open(BASE_IMAGE_PATH).convert("RGBA")
    bw, bh = base.size

    if int(calib["width"]) != bw or int(calib["height"]) != bh:
        raise RuntimeError(
            f"[ERROR] base image size {bw}x{bh} != calib {calib['width']}x{calib['height']}. "
            f"Base image must be same frame/size as calibration."
        )

    center_lat = float(calib["center_lat"])
    center_lon = float(calib["center_lon"])
    scale = float(calib["scale"])

    draw = ImageDraw.Draw(base)

    for p in PLACES_RAW:
        lat, lon = naver_xy_to_latlon(p["coords"]["x"], p["coords"]["y"])
        x, y = latlon_to_image_px_calibrated(lat, lon, center_lat, center_lon, scale, bw, bh)
        inside = (0 <= x < bw) and (0 <= y < bh)
        print(f"[pin] {p['label']} lat={lat:.6f} lon={lon:.6f} -> px=({x},{y}) inside={inside}")
        draw_number_pin(draw, x, y, p["label"])

    base.save(OUTPUT_PATH)
    print(f"✅ saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
