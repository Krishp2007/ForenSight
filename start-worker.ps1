$env:PYTHONPATH     = "d:\ForenSight\ForenSight"
$env:SCAPY_CACHE_DIR = "$env:TEMP\scapy_cache_forensight"

# Remove locked scapy cache if exists
Remove-Item "$env:USERPROFILE\.cache\scapy" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "$env:TEMP\scapy_cache_forensight" -Force | Out-Null

Set-Location "d:\ForenSight\ForenSight\backend"
Write-Host "=== ForenSight Celery Worker ===" -ForegroundColor Yellow
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host "Starting worker..." -ForegroundColor Green

& ".venv\Scripts\python.exe" -m celery -A backend.app.worker.celery_app worker `
    --loglevel=info `
    --concurrency=1 `
    --pool=solo
