# syntax=docker/dockerfile:1.7

########################
# 1) builder: wheels
########################
FROM python:3.11-slim AS builder
WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt


########################
# 2) runtime: run deps
########################
FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 핵심: libgomp1 (Paddle / OpenMP runtime) - API에서는 필요 없을 수 있으나 공통 기반 유지를 위해 남김
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# 소스 복사 (API는 AI 제외)
COPY backend /app/backend
COPY README.md /app/README.md

# backend 패키지 인식용 파일 생성 (이미 backend 폴더 카피로 해결되지만 안전장치)
RUN set -eu; \
    touch /app/backend/__init__.py

########################
# 3) api-final: non-root
########################
FROM runtime AS api-final

RUN useradd -m -u 10001 appuser
USER 10001

# 실행 커맨드는 k8s deployment.yaml나 docker-compose 등에서 정의
EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
