#!/bin/bash

# Set Python module search path
export PYTHONPATH=/app

echo "🚀 Starting ForenSight AI FastAPI Backend on 127.0.0.1:8000..."
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level info &
UVICORN_PID=$!

# Wait for Uvicorn process to initialize
sleep 3

if kill -0 $UVICORN_PID 2>/dev/null; then
    echo "✅ FastAPI Backend is running (PID $UVICORN_PID)!"
else
    echo "❌ ERROR: FastAPI Backend failed to start or crashed on startup!"
fi

# Dynamically configure Nginx port if Render passed a custom $PORT
if [ -n "$PORT" ] && [ "$PORT" != "80" ] && [ "$PORT" != "10000" ]; then
    echo "🔧 Configuring Nginx to listen on Render PORT $PORT..."
    sed -i "s/listen 80;/listen 80;\n    listen $PORT;/g" /etc/nginx/conf.d/default.conf
fi

echo "🌐 Starting Nginx Frontend Web Server..."
nginx -g "daemon off;"
