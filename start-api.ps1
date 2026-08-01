$env:PYTHONPATH = "d:\ForenSight\ForenSight"
Set-Location "d:\ForenSight\ForenSight\backend"
Write-Host "Starting ForenSight API on http://localhost:8000" -ForegroundColor Green
& ".venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
