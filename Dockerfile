# Multi-stage build for ProofMind AI (Frontend + Backend in a Single Container)

# Stage 1: Build the React + TypeScript + Vite Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
# Empty VITE_API_BASE_URL enables relative same-origin API calls (/health, /analyze, etc.)
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Production Python Backend + FastAPI + PyMuPDF + ChromaDB
FROM python:3.11-slim
WORKDIR /app

# Install system build dependencies for PyMuPDF and SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ ./backend/
COPY demo-data/ ./demo-data/

# Copy built frontend static assets from Stage 1 into frontend/dist
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Ensure persistent storage directory exists and set user 1000 permissions for Hugging Face Spaces
RUN useradd -m -u 1000 user && \
    mkdir -p /app/backend/storage && \
    chown -R user:user /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

ENV PORT=7860
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

# Default port (7860 is standard for Hugging Face Spaces; Koyeb/Render pass $PORT dynamically)
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-7860}"]

