# ── Stage 1: Build Frontend ─────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /build

COPY app/frontend/package*.json ./
RUN npm ci

COPY app/frontend ./
RUN npm run build

# ── Stage 2: Application Runtime ────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_PROVIDER=mock \
    REQUIRE_API_KEY=false

WORKDIR /workspace

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY app/pyproject.toml /workspace/app/
COPY pyproject.toml /workspace/
RUN pip install --no-cache-dir -e ./app

# Copy application source
COPY app /workspace/app

# Copy compiled frontend from Stage 1 into app/frontend/dist
COPY --from=frontend-builder /build/dist /workspace/app/frontend/dist

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
