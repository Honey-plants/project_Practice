"""
KAKAO MAP – KOREA FULL MAP (FIXED FRAME)
- 한국 전체 지도(한글) 고정
- 네이버 coords (x,y) -> lat/lon 변환
- 핀 찍힌 지도 PNG 생성
- Playwright로 JS StaticMap 캡쳐

사전 준비:
  pip install playwright
  python -m playwright install chromium

카카오 개발자 콘솔:
  - 카카오맵 사용 ON
  - Web 플랫폼 도메인 추가: http://127.0.0.1:8009
  - JavaScript 키 사용 (REST 키 ❌)

실행:
  python get_kakao_korea_full_map.py

결과:
  kakao_korea_full.png
"""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

# =========================
# 🔑 CONFIG
# =========================
KAKAO_JAVASCRIPT_KEY = "127127b40c57552759a57dc996138006"

# 👉 한국 전체 지도 고정 값 (중요)
KOREA_CENTER_LAT = 36.5
KOREA_CENTER_LON = 127.8
KOREA_LEVEL = 13        # 7~8 추천 (8 = 제주 포함)

WIDTH, HEIGHT = 900, 520
PORT = 8009
OUT_PATH = "kakao_korea_level_13.png"


# =========================
# NAVER coords → (lat, lon)
# =========================
def naver_xy_to_latlon(x: str, y: str):
    lon = float(x) / 1e7
    lat = float(y) / 1e7
    return lat, lon


# ✅ 네가 준 좌표
VISITS_NAVER = [
    {"x": "1277400846", "y": "378573820"},
]

VISITS = [naver_xy_to_latlon(v["x"], v["y"]) for v in VISITS_NAVER]


# =========================
# HTML 생성
# =========================
def build_html(latlons):
    markers_js = ",\n".join(
        f'{{ position: new kakao.maps.LatLng({lat}, {lon}), text: "{i+1}" }}'
        for i, (lat, lon) in enumerate(latlons)
    )

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{ margin:0; padding:0; background:#fff; }}
    #staticMap {{ width:{WIDTH}px; height:{HEIGHT}px; }}
  </style>
</head>
<body>
  <div id="staticMap"></div>

  <script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JAVASCRIPT_KEY}"></script>
  <script>
    const container = document.getElementById('staticMap');

    const markers = [
      {markers_js}
    ];

    const options = {{
      center: new kakao.maps.LatLng({KOREA_CENTER_LAT}, {KOREA_CENTER_LON}),
      level: {KOREA_LEVEL},
      marker: markers
    }};

    new kakao.maps.StaticMap(container, options);

    // Playwright 캡쳐 신호
    setTimeout(() => {{
      document.body.setAttribute("data-ready", "1");
    }}, 1000);
  </script>
</body>
</html>
"""


# =========================
# Local server
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        html = build_html(VISITS).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *args):
        return


def start_server():
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


# =========================
# Main
# =========================
def main():
    if "YOUR_KAKAO_JAVASCRIPT_KEY" in KAKAO_JAVASCRIPT_KEY:
        raise RuntimeError("KAKAO_JAVASCRIPT_KEY에 카카오 JavaScript 키를 넣어줘.")

    # 좌표 변환 로그
    for lat, lon in VISITS:
        print(f"PIN at lat={lat:.6f}, lon={lon:.6f}")

    threading.Thread(target=start_server, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        page.goto(f"http://127.0.0.1:{PORT}/", wait_until="load")
        page.wait_for_selector('body[data-ready="1"]', timeout=15000)

        page.locator("#staticMap").screenshot(path=OUT_PATH)
        browser.close()

    print(f"✅ saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
