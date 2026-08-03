# ── ForenSight AI — Backend Dockerfile ──────────────────────────────────────
# Runs both the FastAPI API server and the Celery worker from the same image.
# The CMD is overridden per-service in docker-compose.yml.

FROM python:3.11-slim

# System deps required by WeasyPrint (Pango/Cairo), python-magic, and Scapy
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Install Python dependencies first (layer cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create storage directories used by the vector store and evidence cache
RUN mkdir -p /app/app/storage/vector_indexes

# Expose FastAPI port
EXPOSE 8000

# Default: run the API server.
# The worker service overrides this CMD in docker-compose.yml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
