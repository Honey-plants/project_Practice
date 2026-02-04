# docker/worker.Dockerfile

FROM python:3.11-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ARG WORKER_REQUIREMENTS=requirements_cpu.txt
ARG PIP_EXTRA_INDEX_URL=""

COPY ${WORKER_REQUIREMENTS} /build/requirements.txt

RUN pip install --upgrade pip && \
    if [ -n "$PIP_EXTRA_INDEX_URL" ]; then \
      pip wheel --no-cache-dir --wheel-dir /wheels -r /build/requirements.txt --extra-index-url "$PIP_EXTRA_INDEX_URL"; \
    else \
      pip wheel --no-cache-dir --wheel-dir /wheels -r /build/requirements.txt; \
    fi

FROM python:3.11-slim AS runtime
WORKDIR /app

RUN useradd -m -u 10001 appuser

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . /app
ENV PYTHONPATH=/app
USER appuser

# Default command; overridden by Helm values (worker.command/args)
CMD ["python", "-m", "AI.menu_assistant.worker.worker_app.main"]
