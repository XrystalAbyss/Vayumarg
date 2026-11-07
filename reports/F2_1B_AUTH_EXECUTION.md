# VAYUMARG — Milestone F2.1B: Live MOSDAC Authentication and Acquisition Report

**Milestone:** F2.1B — Live MOSDAC Authentication, Exact-Granule Acquisition and Scientific Acceptance  
**Timestamp:** 2026-11-01T20:15:00+05:30  
**Status:** **VERIFIED_SUCCESS**  
**Author:** Principal Satellite Data Engineer, Windows Security Reviewer & QA Lead  

---

## 1. Executive Summary

Milestone F2.1B achieved the first successful, authenticated live acquisition of an authentic ISRO INSAT-3DR Level-1B satellite granule from the official MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre) portal without persistent credential storage, using owner-authorized credentials (`ishhangoyal`).

The acquired scene captures **Cyclone REMAL** at its official IMD peak landfall crossing window (**2024-05-26 18:02 UTC**).

---

## 2. Security & Credential Hygiene Architecture

The acquisition pipeline enforces strict security guarantees adhering to defense-in-depth principles:

1. **Zero Credential Persistence:**
   - No credentials stored in `.env`, Git repository, configuration files, or build artifacts.
   - Credentials passed strictly via ephemeral environment variables (`MOSDAC_USERNAME`, `MOSDAC_PASSWORD`) or interactive masking.
2. **Ephemeral Sandbox Isolation:**
   - Isolated staging directory created outside the project tree: `C:\Users\astra\AppData\Local\Temp\vayumarg_mosdac_*`.
   - Windows DACL restrictions applied using PowerShell/Windows API (`icacls` / `Set-Acl`), granting access exclusively to the current executing user SID and stripping inheritance.
3. **Multi-Pass Overwrite & Cleanup:**
   - Temporary `config.json` is wiped with multi-pass random/zero overwrites (`secure_wipe_file`) before file unlinking.
   - Entire temporary directory tree is unlinked and verified deleted post-acquisition.
   - Directory deletion verified: `Test-Path <temp_dir> -> False`.

---

## 3. API Execution & Socket Read Hardening

### 3.1 Granule Targeting & Query Parameters
- **Target Dataset:** `3RIMG_L1B_STD` (INSAT-3DR Imager Level-1B Standard)
- **Granule Record ID (`gId`):** `13623453`
- **Granule Identifier:** `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`
- **Acquisition Timestamp:** `2024-05-26T18:02:00Z`
- **Target Location:** `data/raw/satellite/insat_real/`

### 3.2 Network Stability Fix (Socket Read Timeout Hardening)
- **Root Cause Identified:** The official MOSDAC client (`mdapi.py`) hardcoded `timeout=5` on `requests.get(download_url, stream=True, timeout=5)`. In `requests`, a scalar timeout applies to every socket chunk read. For a 280 MB file with 1 MB chunks (`chunk_size=1048576`), any momentary network hesitation (> 5.0s) raised `ReadTimeout`, causing `mdapi.py` to delete the partial file and restart.
- **Architectural Hotfix:** Hardened `SecureMOSDACDownloader` to automatically patch copied execution scripts with `timeout=(15, 120)` (15s connect timeout, 120s chunk read timeout).
- **Outcome:** Streamed full 280.64 MB payload continuously at ~2.7 MB/s without interruption.

---

## 4. Execution Telemetry

```
============================================================
      VAYUMARG SECURE MOSDAC SATELLITE ACQUISITION         
============================================================

Querying MOSDAC catalog for 3RIMG_L1B_STD (2024-05-26 to 2024-05-26)...
Found 1 total results (280.00 MB) for 3RIMG_L1B_STD
Targeting exact granule: gId=13623453 | expected_file=3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5
Starting isolated MOSDAC acquisition subprocess in C:\Users\astra\AppData\Local\Temp\vayumarg_mosdac_cvqu3r3e...
MOSDAC process exited with code 0

[SUCCESS] Acquisition completed! 1 file(s) saved.
 - data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5 (280.64 MB)
```

---

## 5. Artifact Verification

| Property | Value |
|---|---|
| **Local File Path** | `data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` |
| **Exact File Size** | `294,275,518 bytes` (280.64 MB) |
| **SHA-256 Checksum** | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` |
| **Sandbox Status** | Successfully wiped; 0 leftover files; 0 persisted secrets |

