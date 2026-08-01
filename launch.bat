@echo off
set PYTHONPATH=d:\ForenSight\ForenSight
cd /d d:\ForenSight\ForenSight\backend
echo Starting ForenSight API...
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
