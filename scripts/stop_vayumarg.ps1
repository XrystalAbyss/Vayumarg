# ==============================================================================
# VAYUMARG -- SAFE APPLICATION TERMINATION SCRIPT
# Stops ONLY positively verified Vayumarg processes
# ==============================================================================

[CmdletBinding()]
param (
    [int]$Port = 8000
)

$ErrorActionPreference = 'Continue'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

Write-Host ''
Write-Host '========================================================================' -ForegroundColor Cyan
Write-Host '   VAYUMARG -- APPLICATION SHUTDOWN MANAGER' -ForegroundColor Yellow
Write-Host '========================================================================' -ForegroundColor Cyan
Write-Host ''

$PidFile = Join-Path $ProjectRoot 'logs\runtime\vayumarg.pid'
$TargetPids = [System.Collections.Generic.List[int]]::new()

# 1. Read Recorded PID if available
if (Test-Path -LiteralPath $PidFile) {
    $RecordedPidText = (Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Out-String).Trim()
    if ($RecordedPidText -match '^\d+$') {
        $pVal = [int]$RecordedPidText
        if (-not $TargetPids.Contains($pVal)) {
            $TargetPids.Add($pVal)
        }
    }
}

# 2. Check Port Listener
try {
    $PortConns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($PortConns) {
        foreach ($conn in $PortConns) {
            if ($conn.OwningProcess -and (-not $TargetPids.Contains($conn.OwningProcess))) {
                $TargetPids.Add($conn.OwningProcess)
            }
        }
    }
} catch {}

if ($TargetPids.Count -eq 0) {
    Write-Host '[INFO] No active Vayumarg process detected on port ' $Port -ForegroundColor Green
    if (Test-Path -LiteralPath $PidFile) {
        Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    }
    exit 0
}

$StoppedCount = 0
foreach ($TargetProcessId in $TargetPids) {
    $proc = Get-Process -Id $TargetProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { continue }

    # Strict safety check: Positively identify Vayumarg before stopping
    $isVayumarg = $false
    try {
        $cimProc = Get-CimInstance Win32_Process -Filter "ProcessId = $TargetProcessId" -ErrorAction SilentlyContinue
        if ($cimProc -and ($cimProc.CommandLine -match "vayumarg\.api\.server" -or $cimProc.CommandLine -match "uvicorn.*vayumarg")) {
            $isVayumarg = $true
        }
    } catch {}

    if (-not $isVayumarg) {
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($health -and $health.status -eq 'OPERATIONAL' -and $health.service -match 'Vayumarg') {
                $isVayumarg = $true
            }
        } catch {}
    }

    if ($isVayumarg) {
        Write-Host ('[*] Positively identified Vayumarg process: ' + $proc.ProcessName + ' (PID: ' + $TargetProcessId + ')') -ForegroundColor Yellow
        Write-Host '    Stopping process...' -ForegroundColor Gray
        Stop-Process -Id $TargetProcessId -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 600
        $StoppedCount++
        Write-Host ('[OK] Vayumarg process (PID: ' + $TargetProcessId + ') stopped cleanly.') -ForegroundColor Green
    } else {
        Write-Host ('[REFUSED] Process ' + $proc.ProcessName + ' (PID: ' + $TargetProcessId + ') is NOT verified as Vayumarg.') -ForegroundColor Red
        Write-Host '          Refusing to terminate unrelated process.' -ForegroundColor Red
    }
}

if (Test-Path -LiteralPath $PidFile) {
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

Write-Host ''
Write-Host '========================================================================' -ForegroundColor Cyan
if ($StoppedCount -eq 0) {
    Write-Host '[INFO] No running Vayumarg process found.' -ForegroundColor Green
} else {
    Write-Host ('   Shutdown complete: ' + $StoppedCount + ' process terminated.') -ForegroundColor Cyan
}
Write-Host '========================================================================' -ForegroundColor Cyan
exit 0
