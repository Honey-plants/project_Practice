from __future__ import annotations
import math
from typing import Tuple

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
