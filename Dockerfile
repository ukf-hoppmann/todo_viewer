FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend
COPY configs configs

ENV HOST=0.0.0.0 \
    PORT=5411 \
    DEV_RELOAD=0

EXPOSE 5411

CMD ["python3", "backend/main.py"]
