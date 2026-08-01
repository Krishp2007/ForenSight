$env:PYTHONPATH = "d:\ForenSight\ForenSight"
Set-Location "d:\ForenSight\ForenSight\backend"
Write-Host "Starting ForenSight Celery Worker" -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m celery -A backend.app.worker.celery_app worker --loglevel=info --concurrency=2 --pool=solo
