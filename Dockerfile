# Stage 1: React-Frontend bauen
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# Stage 2: Backend, liefert API und das gebaute Frontend aus
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
# pip 24.0 aus dem Basis-Image hängt zeitweise beim Index von watchfiles; aktuelles pip nicht
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY configs configs
COPY --from=web /web/dist web/dist

ENV HOST=0.0.0.0 \
    PORT=5411 \
    DEV_RELOAD=0

EXPOSE 5411

CMD ["python3", "backend/main.py"]
