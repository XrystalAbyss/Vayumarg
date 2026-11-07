# ==============================================================================
# VAYUMARG — NOOR 2K26 HACKATHON DEMO LAUNCHER
# One-Command Reproducible Launch for Windows PowerShell
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   VAYUMARG - CYCLONE INTELLIGENCE STUDIO (NOOR 2K26 RELEASE)" -ForegroundColor Yellow
Write-Host "   Authentic Satellite Analytics & Deterministic Forecast Engine" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# 1. Check Python virtual environment
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[!] Virtual environment not found at .venv. Looking for system python..." -ForegroundColor Yellow
    $PythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if (-not $PythonExe) {
        Write-Error "Python executable not found. Please activate or configure .venv."
        exit 1
    }
}
Write-Host "[OK] Using Python: $PythonExe" -ForegroundColor Green

# 2. Check Database connectivity
Write-Host "[*] Checking PostgreSQL PostGIS connectivity on port 5433..." -ForegroundColor Cyan
$DbTest = & $PythonExe -c "
import socket
s = socket.socket()
s.settimeout(1.5)
try:
    s.connect(('127.0.0.1', 5433))
    s.close()
    print('CONNECTED')
except Exception:
    print('OFFLINE')
"

if ($DbTest -match "CONNECTED") {
    Write-Host "[OK] PostgreSQL PostGIS (port 5433) is ONLINE and reachable." -ForegroundColor Green
} else {
    Write-Host "[WARN] PostgreSQL is OFFLINE. Activating OFFLINE DEMO MODE (data/demo_cache/)." -ForegroundColor Yellow
    Write-Host "       All 4 demo cyclones (BIPARJOY, AMPHAN, DANA, REMAL) will serve from local authentic cache." -ForegroundColor Yellow
}

# 3. Check Authentic Satellite Crops
$CropsDir = Join-Path $ProjectRoot "data\processed\satellite\crops"
$CropCount = (Get-ChildItem -Path $CropsDir -Filter "*.h5" -ErrorAction SilentlyContinue).Count
Write-Host "[OK] Authentic INSAT HDF5 crops found: $CropCount" -ForegroundColor Green

# 4. Start Backend Server
Write-Host ""
Write-Host "[*] Starting Vayumarg FastAPI Operational Server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
$ServerJob = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "vayumarg.api.server:app", "--host", "127.0.0.1", "--port", "8000" -PassThru

# 5. Wait for server readiness
$MaxRetries = 15
$Ready = $false
for ($i = 1; $i -le $MaxRetries; $i++) {
    Start-Sleep -Milliseconds 800
    try {
        $Response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($Response.status -eq "OPERATIONAL") {
            $Ready = $true
            break
        }
    } catch {
        # Retry
    }
    Write-Host "    Waiting for server... ($i/$MaxRetries)" -ForegroundColor Gray
}

if (-not $Ready) {
    Write-Host "[!] Server health check did not respond in time." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Backend Server is OPERATIONAL!" -ForegroundColor Green
}

# 6. Launch Browser
Write-Host ""
Write-Host "------------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  Opening Vayumarg Cyclone Intelligence Studio in browser..." -ForegroundColor Yellow
Write-Host "  URL: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------------------" -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000/"

Write-Host ""
Write-Host "Press Ctrl+C to stop the application server." -ForegroundColor White

try {
    Wait-Process -Id $ServerJob.Id
} finally {
    if ($ServerJob -and -not $ServerJob.HasExited) {
        Write-Host "`nStopping server..." -ForegroundColor Yellow
        Stop-Process -Id $ServerJob.Id -Force -ErrorAction SilentlyContinue
    }
}
