# ── ForenSight AI — Unified Single-Container Dockerfile for Render ─────────────────
# Multi-stage build:
# Stage 1: Node.js builds the React SPA frontend
# Stage 2: Python 3.11 + Nginx serves both frontend & runs FastAPI backend

# ── Stage 1: Build Frontend SPA ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Unified Production Container ─────────────────────────────────────
FROM python:3.11-slim

# System dependencies required by Nginx, WeasyPrint, python-magic, and Scapy
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libmagic1 \
    libpcap-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

# Copy application source
COPY backend/ ./backend/

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Create storage directories
RUN mkdir -p /app/backend/app/storage/vector_indexes

# Copy startup script
COPY start-all.sh /app/start-all.sh
RUN sed -i 's/\r$//' /app/start-all.sh && chmod +x /app/start-all.sh

EXPOSE 80 8000

CMD ["/app/start-all.sh"]
