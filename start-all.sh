#!/bin/bash
set -e

# Set Python module search path so backend.app imports resolve correctly
export PYTHONPATH=/app

echo "🚀 Starting ForenSight AI FastAPI Backend on 127.0.0.1:8000..."
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level info &

# Wait for Uvicorn background process to bind to port 8000
sleep 3

echo "🌐 Starting Nginx Frontend Web Server..."
nginx -g "daemon off;"
