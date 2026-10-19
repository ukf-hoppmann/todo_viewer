# Stage 1: React-Frontend bauen
FROM node:22-alpine AS web
WORKDIR /web
COPY src_old/web/package.json src_old/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY src_old/web/ ./
RUN npm run build

# Stage 2: Backend, liefert API und das gebaute Frontend aus
FROM python:3.11-slim
WORKDIR /app

COPY src_old/backend/requirements.txt src_old/backend/requirements.txt
# pip 24.0 aus dem Basis-Image hängt zeitweise beim Index von watchfiles; aktuelles pip nicht
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r src_old/backend/requirements.txt

COPY src_old/backend src_old/backend
COPY configs configs
COPY --from=web /web/dist src_old/web/dist

ENV HOST=0.0.0.0 \
    PORT=5412 \
    DEV_RELOAD=0

EXPOSE 5412

CMD ["python3", "src_old/backend/main.py"]
