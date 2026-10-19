# Neubau des ToDo-Viewers (EPIC-007): Server und Client in einem Image.
# Gebaut wird vom Projektordner aus: docker build -f server/Dockerfile .  (docker compose: Dienst todo-viewer-next)

# Stage 1: Client bauen (vite build; Typen und Lint prüft scripts/check-next.sh, nicht das Image)
FROM node:22-alpine AS client
WORKDIR /build/client
COPY client/package.json client/package-lock.json client/.npmrc ./
RUN npm ci --no-audit --no-fund --ignore-scripts
COPY client/ ./
RUN npx vite build --config configs/vite/vite.config.ts

# Stage 2: Server, liefert API, MCP und das gebaute Frontend aus
FROM python:3.11-slim
WORKDIR /app
COPY server/pyproject.toml server/constraints.txt server/
COPY server/src server/src
# Die getesteten Versionen (constraints.txt); pip aus dem Basis-Image hängt zeitweise, darum aktuell.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -c server/constraints.txt ./server \
 && rm -rf server
COPY --from=client /build/client/dist client/dist

ENV VIEWER_HOST=0.0.0.0 \
    VIEWER_PORT=5411 \
    VIEWER_DB=/app/configs/viewer.db \
    VIEWER_BACKUP_DIR=/app/configs/backups \
    VIEWER_LOG_DIR=/app/logs \
    VIEWER_STATIC_DIR=/app/client/dist

EXPOSE 5411

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5411/api/core/health', timeout=4)"

CMD ["python", "-m", "viewer.app.main"]
