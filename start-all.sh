#!/bin/bash

# Set Python module search path
export PYTHONPATH=/app

# ── 512MB RAM Optimization Environment Rules ──
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONMALLOC=malloc

# Dynamically configure Nginx port if Render passed a custom $PORT
TARGET_PORT="${PORT:-10000}"
echo "🔧 Configuring Nginx port binding (PORT: $TARGET_PORT)..."
if [ -f /etc/nginx/conf.d/default.conf ]; then
    sed -i "s/listen 10000;/listen $TARGET_PORT;/g" /etc/nginx/conf.d/default.conf
    sed -i "s/listen 80;/listen 80;\n    listen $TARGET_PORT;/g" /etc/nginx/conf.d/default.conf
fi

echo "🌐 Starting Nginx Web Server immediately so Render port scanner detects open port..."
nginx

echo "🚀 Launching ForenSight AI FastAPI Backend Supervisor on 127.0.0.1:8000..."

# Start Uvicorn supervisor loop in foreground
while true; do
    python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 1 --log-level info
    EXIT_CODE=$?
    echo "⚠️ Uvicorn process exited with status $EXIT_CODE. Restarting in 2 seconds..."
    sleep 2
done
