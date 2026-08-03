# ForenSight - Start Everything
# Run: powershell -ExecutionPolicy Bypass -File start-all.ps1

$root     = "d:\ForenSight\ForenSight"
$backend  = "$root\backend"
$frontend = "$root\frontend"

Write-Host "=== ForenSight Startup ===" -ForegroundColor Cyan

# Kill any stale process on port 8000
$pids = (netstat -ano | Select-String ":8000.*LISTENING") -replace '.*\s(\d+)$','$1'
foreach ($p in $pids) {
    if ($p -match '^\d+$') {
        Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue
        Write-Host "  Killed stale process $p on :8000" -ForegroundColor Gray
    }
}
Start-Sleep -Seconds 1

# 1. Docker (MongoDB, Neo4j, Redis, MinIO)
Write-Host "[1/3] Starting Docker services..." -ForegroundColor Yellow
docker compose -f "$root\docker-compose.yml" up -d
Write-Host "      Done." -ForegroundColor Green

# 2. Backend API
Write-Host "[2/3] Starting API (http://localhost:8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:PYTHONPATH='$root'; Set-Location '$backend'; " +
    "Write-Host 'API: http://localhost:8000/docs' -ForegroundColor Cyan; " +
    ".venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
) -WindowStyle Normal
Write-Host "      API window opened." -ForegroundColor Green

# 3. Frontend
Write-Host "[3/3] Starting frontend (http://localhost:5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$frontend'; npm run dev"
) -WindowStyle Normal
Write-Host "      Frontend window opened." -ForegroundColor Green

Write-Host ""
Write-Host "All services started." -ForegroundColor Green
Write-Host "  App : http://localhost:5173" -ForegroundColor White
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor White
