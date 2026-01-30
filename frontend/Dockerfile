# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build && \
    if [ -d dist ]; then cp -r dist /out; \
    elif [ -d build ]; then cp -r build /out; \
    else echo "No build output (dist/build) found"; ls -la; exit 1; fi

FROM nginx:alpine AS runtime
COPY --from=build /out /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
