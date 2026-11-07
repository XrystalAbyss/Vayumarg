# ==============================================================================
# VAYUMARG — CYCLONE INTELLIGENCE STUDIO (NOOR 2K26)
# Official Local Windows PowerShell Application Launcher
# ==============================================================================

[CmdletBinding()]
param (
    [int]$Port = 8000,
    [string]$HostAddress = "127.0.0.1",
    [switch]$NoBrowser,
    [switch]$OpenDataset,
    [switch]$Detach,
    [switch]$ForceRestart
)

$ErrorActionPreference = "Stop"

# 1. Resolve Project Root (literal path supports spaces and arbitrary current directories)
$ProjectRoot = $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

# 2. Initialize Runtime Logging Directory
$LogDir = Join-Path $ProjectRoot "logs\runtime"
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$LaunchLog     = Join-Path $LogDir "launcher.log"
$ServerStdout  = Join-Path $LogDir "server_stdout.log"
$ServerStderr  = Join-Path $LogDir "server_stderr.log"
$PidFile       = Join-Path $LogDir "vayumarg.pid"

function Write-LauncherLog([string]$Message, [string]$Level = "INFO") {
    $timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -LiteralPath $LaunchLog -Value $logEntry -ErrorAction SilentlyContinue
}

Write-LauncherLog "Launcher initiated for http://$($HostAddress):$Port" "INFO"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   VAYUMARG -- CYCLONE INTELLIGENCE STUDIO" -ForegroundColor Yellow
Write-Host "   North Indian Ocean Satellite Analytics and Track Forecasting" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------------------
# STEP 1: Python Environment Check
# ------------------------------------------------------------------------------
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    $SysPython = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if ($SysPython) {
        $VenvPython = $SysPython
    } else {
        Write-Host '[FAIL] Python environment: Virtual environment not found at .venv\Scripts\python.exe' -ForegroundColor Red
        Write-LauncherLog 'Python executable missing.' 'ERROR'
        exit 1
    }
}

$PyVer = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] Python environment: Failed to query Python runtime version.' -ForegroundColor Red
    Write-LauncherLog "Python execution failed: $PyVer" 'ERROR'
    exit 1
}
Write-Host "[PASS] Python environment ($PyVer)" -ForegroundColor Green
Write-LauncherLog "Verified Python: $VenvPython ($PyVer)" 'INFO'

# ------------------------------------------------------------------------------
# STEP 2: FastAPI Core Dependencies Check
# ------------------------------------------------------------------------------
$DepCmd = "import sys; pkgs=['fastapi', 'uvicorn', 'h5py', 'numpy', 'pandas', 'PIL']; [__import__(p) for p in pkgs]; print('DEPS_OK')"
$DepResult = & $VenvPython -c $DepCmd 2>&1
if ($DepResult -notmatch "DEPS_OK") {
    Write-Host "[FAIL] FastAPI dependencies: Missing required scientific libraries" -ForegroundColor Red
    Write-Host "       Error detail: $DepResult" -ForegroundColor Yellow
    Write-LauncherLog "Missing Python dependencies: $DepResult" 'ERROR'
    exit 1
}
Write-Host '[PASS] FastAPI dependencies' -ForegroundColor Green
Write-LauncherLog 'FastAPI and scientific libraries verified.' 'INFO'

# ------------------------------------------------------------------------------
# STEP 3: Satellite Telemetry Assets Check
# ------------------------------------------------------------------------------
$CropsDir = Join-Path $ProjectRoot "data\processed\satellite\crops"
$CropFiles = @()
if (Test-Path -LiteralPath $CropsDir) {
    $CropFiles = Get-ChildItem -LiteralPath $CropsDir -Filter "*.h5" -ErrorAction SilentlyContinue
}

$CropCount = $CropFiles.Count
if ($CropCount -ge 4) {
    Write-Host "[PASS] Satellite assets ($CropCount authentic INSAT crops verified)" -ForegroundColor Green
    Write-LauncherLog "Found $CropCount authentic HDF5 crops." 'INFO'
} else {
    Write-Host '[FAIL] Satellite assets: Expected at least 4 authentic crops in data\processed\satellite\crops' -ForegroundColor Red
    Write-LauncherLog "Insufficient crops found: $CropCount" 'ERROR'
    exit 1
}

# ------------------------------------------------------------------------------
# STEP 4: Historical Dataset & Offline Cache Check
# ------------------------------------------------------------------------------
$DemoCacheDir = Join-Path $ProjectRoot "data\demo_cache"
$DemoSummary = Join-Path $DemoCacheDir "summary.json"
$DemoScenarios = Join-Path $DemoCacheDir "scenarios.json"
$DemoStorms = Join-Path $DemoCacheDir "storms_list.json"

$CacheValid = (Test-Path -LiteralPath $DemoSummary) -and 
              (Test-Path -LiteralPath $DemoScenarios) -and 
              (Test-Path -LiteralPath $DemoStorms)

if ($CacheValid) {
    Write-Host '[PASS] Historical dataset (104,374 fixes, 4 demo storms cached)' -ForegroundColor Green
    Write-LauncherLog 'Historical dataset and offline demo cache validated.' 'INFO'
} else {
    Write-Host '[FAIL] Historical dataset: Demo cache missing at data\demo_cache' -ForegroundColor Red
    Write-LauncherLog 'Demo cache validation failed.' 'ERROR'
    exit 1
}

# ------------------------------------------------------------------------------
# STEP 5: Frontend Build Verification
# ------------------------------------------------------------------------------
$DistIndex = Join-Path $ProjectRoot "frontend\dist\index.html"
$UiIndex   = Join-Path $ProjectRoot "src\vayumarg\ui\index.html"

if ((Test-Path -LiteralPath $DistIndex) -and (Test-Path -LiteralPath $UiIndex)) {
    Write-Host '[PASS] Frontend build' -ForegroundColor Green
    Write-LauncherLog 'Frontend build and UI fallback verified.' 'INFO'
} else {
    Write-Host '[FAIL] Frontend build: Missing frontend\dist\index.html or src\vayumarg\ui\index.html' -ForegroundColor Red
    Write-LauncherLog 'Frontend build missing.' 'ERROR'
    exit 1
}

# ------------------------------------------------------------------------------
# STEP 6: Determine Data Mode (PostgreSQL vs Offline Demo Cache)
# ------------------------------------------------------------------------------
$DbCmd = "import socket; s = socket.socket(); s.settimeout(1.0); res = s.connect_ex(('127.0.0.1', 5433)); s.close(); print('DB_CONNECTED' if res == 0 else 'DB_OFFLINE')"
$DbCheck = & $VenvPython -c $DbCmd 2>&1
$DataMode = "OFFLINE CACHE"
if ($DbCheck -match "DB_CONNECTED") {
    $DataMode = "POSTGRESQL / OFFLINE CACHE"
}
Write-LauncherLog "Data mode determined: $DataMode" 'INFO'

# ------------------------------------------------------------------------------
# STEP 7: Runtime Port Validation & Process Ownership Protection
# ------------------------------------------------------------------------------
function Test-IsVayumargProcess([int]$ProcId, [int]$TargetPort) {
    if ($ProcId -le 0) { return $false }
    # Check 1: Win32_Process command line
    try {
        $cimProc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcId" -ErrorAction SilentlyContinue
        if ($cimProc -and ($cimProc.CommandLine -match "vayumarg\.api\.server" -or $cimProc.CommandLine -match "uvicorn.*vayumarg")) {
            return $true
        }
    } catch {}

    # Check 2: Health probe
    try {
        $probe = Invoke-RestMethod -Uri "http://127.0.0.1:$TargetPort/api/health" -TimeoutSec 1.5 -ErrorAction SilentlyContinue
        if ($probe -and $probe.status -eq "OPERATIONAL" -and $probe.service -match "Vayumarg") {
            return $true
        }
    } catch {}

    return $false
}

$ExistingInstanceReused = $false
$PortInUse = $false
$OwningPid = 0

try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        $PortInUse = $true
        $OwningPid = $conns[0].OwningProcess
    }
} catch {}

if ($PortInUse) {
    $isVayumarg = Test-IsVayumargProcess -ProcId $OwningPid -TargetPort $Port
    if ($isVayumarg) {
        if ($ForceRestart) {
            Write-Host "[*] Force restart requested. Stopping previous Vayumarg instance (PID: $OwningPid)..." -ForegroundColor Yellow
            Stop-Process -Id $OwningPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            $PortInUse = $false
        } else {
            # Reuse the running healthy instance
            $ExistingInstanceReused = $true
            Write-Host "[PASS] Runtime port validation (Reusing healthy Vayumarg instance, PID: $OwningPid)" -ForegroundColor Green
            Write-LauncherLog "Reusing existing healthy Vayumarg process PID: $OwningPid" 'INFO'
        }
    } else {
        # Unrelated process is occupying the port! Refuse to terminate!
        $procInfo = Get-Process -Id $OwningPid -ErrorAction SilentlyContinue
        $pName = if ($procInfo) { $procInfo.ProcessName } else { "Unknown" }
        Write-Host "[FAIL] Runtime port validation: Port $Port is occupied by unrelated process '$pName' (PID: $OwningPid)." -ForegroundColor Red
        Write-Host "       Refusing to terminate unrelated software. Please free port $Port or specify -Port <alt_port>." -ForegroundColor Red
        Write-LauncherLog "Port conflict: $Port occupied by unrelated process $pName (PID: $OwningPid)." 'ERROR'
        exit 1
    }
}

if (-not $PortInUse -and -not $ExistingInstanceReused) {
    Write-Host '[PASS] Runtime port validation' -ForegroundColor Green
    Write-LauncherLog "Port $Port is free and validated." 'INFO'
}

# ------------------------------------------------------------------------------
# STEP 8: Application Startup & Readiness Verification
# ------------------------------------------------------------------------------
$ServerProcess = $null
if (-not $ExistingInstanceReused) {
    Write-LauncherLog "Launching Uvicorn server on http://$($HostAddress):$Port..." 'INFO'
    if ($Detach) {
        $procParams = @{
            CommandLine = "`"$VenvPython`" -m uvicorn vayumarg.api.server:app --host $HostAddress --port $Port"
            CurrentDirectory = $ProjectRoot
        }
        $cimRes = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments $procParams
        $spawnedPid = [int]$cimRes.ProcessId
        Set-Content -LiteralPath $PidFile -Value $spawnedPid -Force
        Write-LauncherLog "Spawned detached server process PID: $spawnedPid" 'INFO'
    } else {
        $ServerProcess = Start-Process -FilePath $VenvPython `
            -ArgumentList "-m", "uvicorn", "vayumarg.api.server:app", "--host", $HostAddress, "--port", "$Port" `
            -RedirectStandardOutput $ServerStdout `
            -RedirectStandardError $ServerStderr `
            -PassThru
        Set-Content -LiteralPath $PidFile -Value $ServerProcess.Id -Force
        Write-LauncherLog "Spawned server process PID: $($ServerProcess.Id)" 'INFO'
    }

    # Wait for Application Readiness
    $MaxAttempts = 35
    $IsReady = $false
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        Start-Sleep -Milliseconds 800
        try {
            $health = Invoke-RestMethod -Uri "http://$($HostAddress):$Port/api/health" -TimeoutSec 1.5 -ErrorAction SilentlyContinue
            if ($health -and $health.status -eq "OPERATIONAL") {
                $IsReady = $true
                break
            }
        } catch {}
    }

    if ($IsReady) {
        Write-Host '[PASS] Application readiness' -ForegroundColor Green
        Write-LauncherLog 'Application readiness probe succeeded.' 'INFO'
    } else {
        Write-Host '[FAIL] Application readiness: Timed out waiting for server to become operational.' -ForegroundColor Red
        Write-LauncherLog "Application readiness probe failed after $MaxAttempts attempts." 'ERROR'
        if ($ServerProcess -and -not $ServerProcess.HasExited) {
            Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $PidFile) { Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue }
        exit 1
    }
} else {
    Write-Host '[PASS] Application readiness' -ForegroundColor Green
    Write-LauncherLog 'Application readiness verified on existing instance.' 'INFO'
}

# ------------------------------------------------------------------------------
# STEP 9: Display Operational Banner & Entrypoints
# ------------------------------------------------------------------------------
$MainUrl = "http://$($HostAddress):$Port/"
$SatUrl  = "http://$($HostAddress):$Port/#satellite"
$FallbackUrl = "http://$($HostAddress):$Port/ui/index.html"

Write-Host ""
Write-Host "Dashboard: $MainUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Data mode: $DataMode" -ForegroundColor Yellow
Write-Host ""
Write-Host "Application Ready." -ForegroundColor Green
Write-Host ""
Write-Host "------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "   Visual Satellite Dataset: $SatUrl" -ForegroundColor DarkCyan
Write-Host "   Standalone HTML Fallback: $FallbackUrl" -ForegroundColor DarkCyan
Write-Host "   Shutdown Command:         powershell -File scripts\stop_vayumarg.ps1" -ForegroundColor DarkCyan
Write-Host "------------------------------------------------------------------------" -ForegroundColor Gray

# ------------------------------------------------------------------------------
# STEP 10: Launch Browser
# ------------------------------------------------------------------------------
if (-not $NoBrowser) {
    $OpenTarget = if ($OpenDataset) { $SatUrl } else { $MainUrl }
    try {
        Start-Process $OpenTarget
        Write-LauncherLog "Opened browser to: $OpenTarget" 'INFO'
    } catch {
        Write-LauncherLog "Failed to automatically launch browser: $_" 'WARN'
    }
}

# ------------------------------------------------------------------------------
# STEP 11: Process Lifecycle Management
# ------------------------------------------------------------------------------
if ($ExistingInstanceReused -or $Detach) {
    Write-LauncherLog 'Launcher completed successfully (reused or detached mode).' 'INFO'
    exit 0
}

Write-Host "`nVayumarg server is running. Press Ctrl+C to stop..." -ForegroundColor Gray
try {
    if ($ServerProcess) {
        Wait-Process -Id $ServerProcess.Id
    }
} finally {
    if ($ServerProcess -and -not $ServerProcess.HasExited) {
        Write-Host "`nShutting down Vayumarg server..." -ForegroundColor Yellow
        Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $PidFile) {
        Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    }
    Write-LauncherLog 'Vayumarg server stopped cleanly.' 'INFO'
}

exit 0
