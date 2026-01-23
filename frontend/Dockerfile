# syntax=docker/dockerfile:1.7

########################
# builder
########################
FROM node:20-alpine AS builder
WORKDIR /build

# 의존성 캐시 최적화: package 파일 먼저
COPY frontend/package*.json ./

# npm 캐시(빌드킷) 사용: 반복 빌드 속도 향상
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# 소스 복사 후 빌드
COPY frontend/ ./

RUN npm run build

# 빌드 결과를 /out 으로 통일 (dist 또는 build 자동 대응)
# NOTE: 폴더 자체가 아니라 "내용"을 /out에 복사해야 index.html이 루트에 위치합니다.
RUN set -eux; \
    mkdir -p /out; \
    if [ -d "dist" ]; then \
      cp -r dist/. /out/; \
    elif [ -d "build" ]; then \
      cp -r build/. /out/; \
    else \
      echo "ERROR: build output folder not found (expected dist/ or build/)"; \
      ls -la; \
      exit 1; \
    fi; \
    test -f /out/index.html


########################
# runtime
########################
FROM nginx:1.27-alpine AS runtime

# SPA 라우팅을 위한 nginx 설정 (try_files)
RUN set -eux; \
    cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
  listen 8080;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  # 정적 파일
  location /assets/ {
    try_files $uri =404;
  }

  # SPA 라우팅: 존재하지 않으면 index.html
  location / {
    try_files $uri $uri/ /index.html;
  }

  # 간단 헬스
  location /health {
    return 200 'ok';
    add_header Content-Type text/plain;
  }
}
EOF

COPY --from=builder /out /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]


########################
# verify (smoke tests)
########################
FROM runtime AS verify

# 1) nginx 설정 유효성
RUN set -eux; nginx -t

# 2) 빌드 산출물 존재 확인
RUN set -eux; test -f /usr/share/nginx/html/index.html


########################
# final (deployable)
########################
FROM runtime AS final
