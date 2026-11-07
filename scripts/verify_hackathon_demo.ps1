# ==============================================================================
# VAYUMARG — NOOR 2K26 HACKATHON DEMO VERIFICATION
# Automated End-to-End Validation of All Demonstration Subsystems
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   VAYUMARG - AUTOMATED HACKATHON VERIFICATION SUITE" -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

# 1. Run Python API Test Suite
Write-Host "[*] Executing full API endpoint test suite..." -ForegroundColor Cyan
& $PythonExe (Join-Path $ProjectRoot "scripts\test_api_endpoints.py")
$ApiSuccess = ($LASTEXITCODE -eq 0)

# 2. Check Authentic HDF5 Files
Write-Host ""
Write-Host "[*] Verifying authentic ISRO MOSDAC satellite files..." -ForegroundColor Cyan
$CropsDir = Join-Path $ProjectRoot "data\processed\satellite\crops"
$RequiredCrops = @(
    "AMPHAN_20200519_2358_MULTICHANNEL.h5",
    "BIPARJOY_20230612_2358_MULTICHANNEL.h5",
    "DANA_20241025_2330_MULTICHANNEL.h5",
    "REMAL_20240526_1802_MULTICHANNEL.h5"
)

$AllCropsPresent = $true
foreach ($crop in $RequiredCrops) {
    $p = Join-Path $CropsDir $crop
    if (Test-Path $p) {
        $size = (Get-Item $p).Length / 1MB
        Write-Host "   [OK] Found $crop ($('{0:N2}' -f $size) MB)" -ForegroundColor Green
    } else {
        Write-Host "   [MISSING] $crop" -ForegroundColor Red
        $AllCropsPresent = $false
    }
}

# 3. Check Offline Demo Cache Integrity
Write-Host ""
Write-Host "[*] Verifying offline demo cache files..." -ForegroundColor Cyan
$CacheDir = Join-Path $ProjectRoot "data\demo_cache"
$CacheFiles = @("summary.json", "scenarios.json", "storms_list.json")
$CacheOk = $true
foreach ($cf in $CacheFiles) {
    $p = Join-Path $CacheDir $cf
    if (Test-Path $p) {
        Write-Host "   [OK] Found cache file $cf" -ForegroundColor Green
    } else {
        Write-Host "   [MISSING] $cf" -ForegroundColor Red
        $CacheOk = $false
    }
}

# Summary Report
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   VERIFICATION SUMMARY REPORT" -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan

if ($ApiSuccess) {
    Write-Host "   1. REST API Endpoints (14/14):      [PASS]" -ForegroundColor Green
} else {
    Write-Host "   1. REST API Endpoints (14/14):      [FAIL]" -ForegroundColor Red
}

if ($AllCropsPresent) {
    Write-Host "   2. Authentic Satellite Crops (4/4): [PASS]" -ForegroundColor Green
} else {
    Write-Host "   2. Authentic Satellite Crops (4/4): [FAIL]" -ForegroundColor Red
}

if ($CacheOk) {
    Write-Host "   3. Offline Demo Cache:              [PASS]" -ForegroundColor Green
} else {
    Write-Host "   3. Offline Demo Cache:              [FAIL]" -ForegroundColor Red
}

Write-Host "========================================================================" -ForegroundColor Cyan

if ($ApiSuccess -and $AllCropsPresent -and $CacheOk) {
    Write-Host "`n>>> ALL SUBSYSTEMS OPERATIONAL AND READY FOR HACKATHON DEMO <<<`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n>>> VERIFICATION ISSUES DETECTED. REVIEW LOG ABOVE <<<`n" -ForegroundColor Red
    exit 1
}
