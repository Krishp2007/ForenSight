@echo off
title ForenSight API

:: Kill any old python processes holding port 8000
echo Killing old API processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

:: Set environment
set PYTHONPATH=d:\ForenSight\ForenSight
cd /d d:\ForenSight\ForenSight\backend

echo Starting ForenSight API on http://localhost:8000
echo Press Ctrl+C to stop.
echo.

.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
