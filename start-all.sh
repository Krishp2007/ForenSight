#!/bin/bash

# Set Python module search path
export PYTHONPATH=/app

echo "🚀 Launching ForenSight AI FastAPI Backend Supervisor on 127.0.0.1:8000..."

# Start Uvicorn in an auto-restart loop so background server stays alive
(
    while true; do
        python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level info
        EXIT_CODE=$?
        echo "⚠️ Uvicorn process exited with status $EXIT_CODE. Restarting in 2 seconds..."
        sleep 2
    done
) &

# Poll backend health check until port 8000 is ready (up to 30 seconds)
echo "⏳ Waiting for FastAPI Backend to initialize..."
MAX_WAIT=30
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    ( (exec 3<>/dev/tcp/127.0.0.1/8000) 2>/dev/null )
    if [ $? -eq 0 ]; then
        echo "✅ FastAPI Backend is up and listening on 127.0.0.1:8000!"
        break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo "⚠️ Warning: Backend initialization taking longer than $MAX_WAIT seconds. Proceeding..."
fi

# Dynamically configure Nginx port if Render passed a custom $PORT
if [ -n "$PORT" ] && [ "$PORT" != "80" ] && [ "$PORT" != "10000" ]; then
    echo "🔧 Configuring Nginx to listen on Render PORT $PORT..."
    sed -i "s/listen 80;/listen 80;\n    listen $PORT;/g" /etc/nginx/conf.d/default.conf
fi

echo "🌐 Starting Nginx Frontend Web Server..."
exec nginx -g "daemon off;"

