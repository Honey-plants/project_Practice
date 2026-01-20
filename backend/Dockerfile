# syntax=docker/dockerfile:1.7

########################
# builder: wheels build
########################
FROM python:3.11-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# requirements only (cache)
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt


########################
# runtime (base)
########################
FROM python:3.11-slim AS runtime
WORKDIR /app

# OS runtime deps (OpenCV/cv2 needs libGL.so.1 + glib, and sometimes X libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# install wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
 && rm -rf /wheels

# copy full repo
COPY . /app

# ------------------------------------------------------------
# Package/Import path stabilization (NO source code changes)
# ------------------------------------------------------------
RUN set -eu; \
    \
    # 1) make backend a python package (for backend.* imports)
    mkdir -p /app/backend; \
    touch /app/backend/__init__.py; \
    \
    # 2) If real code is in /app/backend/app, expose it also as top-level /app/app
    if [ -d "/app/backend/app" ] && [ ! -e "/app/app" ]; then \
      ln -s /app/backend/app /app/app; \
    fi; \
    \
    # 3) If real code is in /app/app, expose it also as /app/backend/app (reverse case)
    if [ -d "/app/app" ] && [ ! -e "/app/backend/app" ]; then \
      ln -s /app/app /app/backend/app; \
    fi; \
    \
    # 4) Ensure app package is importable even if it was a plain folder
    if [ -d "/app/backend/app" ]; then \
      touch /app/backend/app/__init__.py || true; \
    fi; \
    if [ -d "/app/app" ] && [ ! -L "/app/app" ]; then \
      touch /app/app/__init__.py || true; \
    fi; \
    \
    # 5) Windows folder name 'AI' -> python import 'ai' compatibility
    if [ -d "/app/AI" ] && [ ! -e "/app/ai" ]; then \
      ln -s /app/AI /app/ai; \
    fi; \
    if [ -d "/app/ai" ] && [ ! -L "/app/ai" ]; then \
      touch /app/ai/__init__.py || true; \
    fi


########################
# verify stage (smoke tests)
# - CI에서 이 stage를 빌드하면, libGL/cv2 문제를 "빌드 단계"에서 즉시 차단
########################
FROM runtime AS verify

# 1) OS 패키지 설치 확인 (재발 시 원인 파악이 빠름)
RUN set -eux; \
    dpkg -l | grep -E 'libgl1|libglib2.0-0|libxrender1|libxext6|libsm6'

# 2) 실제 동작 확인: 동적 링크가 해결되어야 import가 성공함
RUN set -eux; \
    python -c "import cv2; print('cv2 OK', cv2.__version__)"

# (선택) OCR까지 강하게 보려면 아래처럼 추가 가능하나, 모델/런타임 비용이 커질 수 있어 기본은 비추천
# RUN set -eux; python -c "from paddleocr import PaddleOCR; print('paddleocr OK')"


########################
# final image (deployable)
########################
FROM runtime AS final

# non-root
RUN useradd -m -u 10001 appuser
USER 10001:10001

EXPOSE 8000

# Keep chart unchanged: uvicorn app.main:app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
