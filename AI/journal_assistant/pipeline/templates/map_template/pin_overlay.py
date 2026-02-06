from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageFilter

from AI.journal_assistant.pipeline.templates.map_template.geo_utils import (
    naver_xy_to_latlon,
    latlon_to_image_px_calibrated,
)

# 여러 색으로 돌려쓰는 팔레트
PIN_COLORS: List[Tuple[int, int, int, int]] = [
    (231, 76, 60, 255),   # red
    (52, 152, 219, 255),  # blue
    (46, 204, 113, 255),  # green
    (155, 89, 182, 255),  # purple
    (241, 196, 15, 255),  # yellow
    (230, 126, 34, 255),  # orange
]

def _cut_white_bg_to_alpha(img_rgba: Image.Image, *, thresh: int = 245) -> Image.Image:
    """
    아이콘 PNG가 투명배경이 아니라 흰 배경이면,
    '거의 흰색' 픽셀을 투명으로 만들어준다.
    """
    rgb = img_rgba.convert("RGB")
    r, g, b = rgb.split()
    # 흰색에 가까울수록 0, 어두울수록 255
    not_white = Image.eval(ImageChops.add(ImageChops.add(r, g), b),
                           lambda v: 0 if v > (thresh * 3) else 255)
    not_white = not_white.filter(ImageFilter.GaussianBlur(0.6))

    out = img_rgba.copy()
    out.putalpha(not_white)
    return out

def load_pin_icon(pin_icon_path: Path, *, width_px: int = 24) -> Image.Image:
    icon = Image.open(pin_icon_path).convert("RGBA")

    # alpha가 완전 불투명하면(=흰 배경일 확률 높음) 컷아웃
    a = icon.getchannel("A")
    if a.getextrema() == (255, 255):
        icon = _cut_white_bg_to_alpha(icon)

    # 너비 기준 리사이즈 (비율 유지)
    w, h = icon.size
    new_w = int(width_px)
    new_h = int(round(h * (new_w / w)))
    return icon.resize((new_w, new_h), Image.LANCZOS)

def tint_icon(icon_rgba: Image.Image, color: Tuple[int, int, int, int]) -> Image.Image:
    """
    원래 아이콘 모양/알파는 유지하고 색만 바꿈
    """
    r, g, b, a = icon_rgba.split()
    solid = Image.new("RGBA", icon_rgba.size, color)
    solid.putalpha(a)
    return solid

def paste_pin_tip_at(base: Image.Image, pin: Image.Image, *, x: int, y: int) -> None:
    """
    핀의 '끝(tip)'이 (x,y)에 오도록 붙임
    """
    w, h = pin.size
    left = int(round(x - w / 2))
    top = int(round(y - h))
    base.alpha_composite(pin, dest=(left, top))

def render_pinned_map_bytes(
    *,
    base_image_path: Path,
    calib_json_path: Path,
    places_raw: List[Dict[str, Any]],
    pin_icon_path: Path,
    pin_width_px: int = 22,  # ✅ 작은 핀
) -> bytes:
    calib = json.loads(calib_json_path.read_text(encoding="utf-8"))

    base = Image.open(base_image_path).convert("RGBA")
    bw, bh = base.size

    if int(calib.get("width")) != bw or int(calib.get("height")) != bh:
        raise RuntimeError(
            f"[ERROR] base image size {bw}x{bh} != calib {calib.get('width')}x{calib.get('height')}. "
            f"Base image must be same frame/size as calibration."
        )

    center_lat = float(calib["center_lat"])
    center_lon = float(calib["center_lon"])
    scale = float(calib["scale"])

    # 최정규 2222

    print("pin_overlay 여긴 언제 오는걸까?")

    # ✅ icon load once
    icon_base = load_pin_icon(pin_icon_path, width_px=pin_width_px)

    for idx, p in enumerate(places_raw):
        lat, lon = naver_xy_to_latlon(p["coords"]["x"], p["coords"]["y"])
        x, y = latlon_to_image_px_calibrated(lat, lon, center_lat, center_lon, scale, bw, bh)

        color = PIN_COLORS[idx % len(PIN_COLORS)]
        pin_colored = tint_icon(icon_base, color)

        inside = (0 <= x < bw) and (0 <= y < bh)
        print(f"[pin] {p.get('label', idx+1)} -> px=({x},{y}) inside={inside}")

        paste_pin_tip_at(base, pin_colored, x=x, y=y)

    from io import BytesIO
    buf = BytesIO()
    base.save(buf, format="PNG")

    # debug 저장 (✅ 동시성 안전)
    if os.getenv("AI_DEBUG_SAVE", "0") == "1":
        out_dir = Path(os.getenv("AI_DEBUG_DIR", "debug_out"))
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"map_with_pin_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}.png"
        (out_dir / fname).write_bytes(buf.getvalue())

    return buf.getvalue()
