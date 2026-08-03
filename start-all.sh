#!/bin/bash
set -e

echo "🚀 Starting ForenSight AI FastAPI Backend..."
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &

echo "🌐 Starting Nginx Frontend Web Server..."
nginx -g "daemon off;"
