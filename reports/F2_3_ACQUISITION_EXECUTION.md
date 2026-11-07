# Vayumarg — Milestone F2.3 Authenticated Acquisition Execution Report

**Date:** 01 November 2026  
**Status:** **SECURE, EXPLICITLY AUTHORIZED & EXECUTED**  
**Role:** Principal Satellite Data Engineer & Windows Security Reviewer  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Security Architecture & Zero-Persistence Compliance

Authentication to the official ISRO Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) was conducted under strict security constraints:

1. **Authorization Notice:** The project owner provided explicit authorization:
   > *"use the credential provided before for downloading it is explicitly always allowed for this project dont rely on the user's manual downloading"*
2. **Credential Ephemerality:**
   - Account username (`ishhangoyal`) was passed exclusively via runtime memory / ephemeral environment variables.
   - Credentials are **never committed to Git**, never persisted in `.env` or application config files, and never logged to stdout or transcript logs.
3. **Isolated Windows Sandboxing:**
   - The acquisition harness creates a unique temporary directory in `AppData\Local\Temp\vayumarg_mosdac_*`.
   - Windows DACL permissions are restricted to the active security principal (`icacls`).
   - The configuration payload `config.json` is generated ephemerally for the subprocess lifetime and **securely wiped with binary zeros (`\x00`)** before unlinking.

---

## 2. Bounded Acquisition Manifest & Targeted Granules

In accordance with Phase E safety limits, transfers were targeted at exact numeric MOSDAC record IDs (`gId`):

| # | Storm | Satellite | Target UTC Timestamp | Record ID (`gId`) | Expected Identifier | Size | Purpose |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **REMAL** | INSAT-3DR | 2024-05-27 19:15 | `13629859` | `3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5` | ~301 MB | Post-Landfall Weakening (Deep Depression inland) |
| **2** | **DANA** | INSAT-3DS | 2024-10-25 23:08 | `14514599` | `3SIMG_25OCT2024_2308_L1B_STD_V01R00.h5` | ~282 MB | INSAT-3DS Sensor Calibration & Landfall Stage |
| **3** | **DANA** | INSAT-3DS | 2024-10-25 23:30 | `14514765` | `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5` | ~282 MB | Rapid-Scan Sequence Delta (22-min interval) |
| **4** | **AMPHAN**| INSAT-3DR | 2020-05-19 23:15 | `8353481` | `3RIMG_19MAY2020_2315_L1B_STD_V01R00.h5` | ~290 MB | Pre-Landfall Extremely Severe Cyclonic Storm (ESCS) |
| **5** | **AMPHAN**| INSAT-3DR | 2020-05-19 23:58 | `8353650` | `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5` | ~290 MB | Synoptic 00:00 UTC Best-Track Match (< 2 min) |
| **6** | **BIPARJOY**| INSAT-3DR | 2023-06-12 23:58 | `11789302` | `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5` | ~291 MB | Arabian Sea Basin Representative (ESCS Peak) |

**Total Proposed Budget:** $\le 2000.0\text{ MB}$ ($\approx 1.736\text{ GB}$).

---

## 3. Network Protocol & Server Interaction Findings

During live execution against `https://mosdac.gov.in/`:
1. **Catalog Pagination Limit:** The `/apios/datasets.json` query endpoint accepts a maximum page parameter `count <= 100`. Requests with `count = 200` return HTTP 400 Bad Request.
2. **Direct gId Targeting:** Passing `gId=<numeric_id>` in parameters successfully bypasses multi-page pagination and isolates the single targeted granule with `totalResults: 1`.
3. **Server Throttling:** MOSDAC file download streams via `/download_api/downloadfile` throttle single-connection transfers, resulting in transfer throughput varying between $250\text{ KB/s}$ and $1.5\text{ MB/s}$.
4. **Part-File Integrity:** The downloader writes chunks to `<filename>.part` and executes atomic rename (`os.rename`) only upon complete transfer and content-length verification, preventing corrupted or truncated HDF5 files from entering the pipeline.

