# syntax=docker/dockerfile:1
# Million Istig'for — Vue (Vite) + FastAPI, Railway production

# --- Stage 1: Vue production build ---
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build

# --- Stage 2: Python runtime ---
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY main.py ./

# app/main.py: parent.parent / "frontend" / "dist"
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN test -f frontend/dist/index.html

EXPOSE 8000

# Railway $PORT; migratsiya avtomatik ishlamaydi (Release Command alohida)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
