# ForenSight — Start Everything
# Run once: right-click → Run with PowerShell
# Or pin to taskbar / add to Startup folder

$root    = "d:\ForenSight\ForenSight"
$backend = "$root\backend"
$frontend = "$root\frontend"

Write-Host "=== ForenSight Startup ===" -ForegroundColor Cyan

# 1. Start Docker infrastructure (MongoDB, Neo4j, Redis, MinIO, Qdrant)
Write-Host "[1/3] Starting Docker services..." -ForegroundColor Yellow
docker compose -f "$root\docker-compose.yml" up -d
Write-Host "      Docker services started." -ForegroundColor Green

# 2. Start API in a new window (stays open, auto-restarts on file change)
Write-Host "[2/3] Starting API server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:PYTHONPATH='$root'; Set-Location '$backend'; Write-Host 'ForenSight API' -ForegroundColor Cyan; .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
) -WindowStyle Normal
Start-Sleep -Seconds 2
Write-Host "      API window opened." -ForegroundColor Green

# 3. Start frontend dev server in a new window
Write-Host "[3/3] Starting frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$frontend'; Write-Host 'ForenSight Frontend' -ForegroundColor Cyan; npm run dev"
) -WindowStyle Normal
Write-Host "      Frontend window opened." -ForegroundColor Green

Write-Host ""
Write-Host "All services starting. Open http://localhost:5173" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Gray
