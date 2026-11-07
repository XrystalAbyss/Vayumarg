# Vayumarg — Milestone F2.3R Six-Granule Acquisition Forensic Reconciliation Report

**Date:** 01 November 2026  
**Status:** **INDEPENDENTLY RECONCILED & DEFECTS CLASSIFIED**  
**Role:** Principal Scientific Data Auditor, Satellite Remote-Sensing Engineer, Security Reviewer  
**Milestone:** F2.3R (Authentic Satellite Acquisition Reconciliation)

---

## 1. Executive Summary & Core Audit Finding

The F2.3 milestone summary reported that an automated batch acquisition driver had been executed for six selected authentic MOSDAC candidate granules. 
This independent audit forensically inspected the filesystem, task execution transcripts, physical file contents, and database records.

**Definitive Scientific Finding:**
- **Zero of the six planned granules completed download successfully.**
- Exactly **one completed authentic granule** exists in the entire project repository (`3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`, 280.64 MB), inherited from Milestone F2.1B.
- Two partial, truncated `.part` files exist in `data/raw/satellite/insat_real/`, both of which fail HDF5 superblock validation and cannot be opened.
- One granule failed to initiate stream transfer.
- Three granules were not attempted.
- **Acquisition Verdict:** **`PARTIAL_ACQUISITION`** (0 of 6 planned files recovered).

---

## 2. Forensic Per-Granule Reconciliation Matrix

| # | Storm | Product | MOSDAC gId | Expected Identifier | Local Status | Size On Disk | Expected Size | HDF5 Valid? | DB Registered? | Final Status |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :-: | :-: | :--- |
| **1** | **REMAL** | 3RIMG_L1B_STD | `13629859` | `3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5` | Truncated `.part` | 31.45 MB | ~381 MB | **NO** | **NO** | **`PARTIAL_DOWNLOAD`** |
| **2** | **DANA** | 3SIMG_L1B_STD | `14514599` | `3SIMG_25OCT2024_2308_L1B_STD_V01R00.h5` | Not present | 0 bytes | ~263 MB | **NO** | **NO** | **`FAILED`** |
| **3** | **DANA** | 3SIMG_L1B_STD | `14514765` | `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5` | Truncated `.part` | 141.56 MB | ~262 MB | **NO** | **NO** | **`PARTIAL_DOWNLOAD`** |
| **4** | **AMPHAN**| 3RIMG_L1B_STD | `8353481` | `3RIMG_19MAY2020_2315_L1B_STD_V01R00.h5` | Not present | 0 bytes | ~290 MB | **NO** | **NO** | **`PLANNED_ONLY`** |
| **5** | **AMPHAN**| 3RIMG_L1B_STD | `8353650` | `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5` | Not present | 0 bytes | ~290 MB | **NO** | **NO** | **`PLANNED_ONLY`** |
| **6** | **BIPARJOY**| 3RIMG_L1B_STD | `11789302` | `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5` | Not present | 0 bytes | ~291 MB | **NO** | **NO** | **`PLANNED_ONLY`** |

---

## 3. Physical Inspection of Truncated Partial Downloads

Testing the two `.part` files with `h5py.File` yielded explicit truncation errors:
1. `3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5.part`:
   - Received bytes: `31,457,280` (exactly 30 MB / 30 chunks).
   - Stored EOF in header: `399,745,097` bytes.
   - Completion: **7.87%**.
   - Error: `OSError: Unable to synchronously open file (truncated file: eof = 31457280, stored_eof = 399745097)`.
2. `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5.part`:
   - Received bytes: `141,557,760` (135 MB / 135 chunks).
   - Stored EOF in header: `275,275,100` bytes.
   - Completion: **51.42%**.
   - Error: `OSError: Unable to synchronously open file (truncated file: eof = 141557760, stored_eof = 275275100)`.

### Root Cause Analysis:
- In `data/tools/mosdac_client/extracted/mdapi.py`, downloads stream over HTTP using `chunk_size = 1048576` (1 MB) into `<filename>.part`.
- The ISRO MOSDAC download endpoint (`/download_api/downloadfile`) throttles single-stream connections to $\sim 150 - 350\text{ KB/s}$, and frequently terminates long-lived sockets after 10–15 minutes.
- When the socket connection dropped mid-stream, `mdapi.py` caught an unhandled read timeout/disconnect, left the incomplete `.part` file on disk, and exited without renaming it to `.h5`.
- **Architectural Safeguard Succeeded:** Because `MultiChannelCropEngine` and `process_acquired_granules.py` filter strictly for valid `.h5` files, **neither corrupted partial file was registered into the PostgreSQL database**. The database remained 100% unpolluted.

---

## 4. Preservation & Recovery Plan for F2.4

In accordance with Section 3.3 ("Do not start new MOSDAC downloads automatically"):
1. **Preservation:** The two `.part` files are retained on disk to document actual transfer behavior and network throughput.
2. **Safe Recovery Architecture for F2.4:**
   - Implement HTTP `Range: bytes=<offset>-` resume headers in `SecureMOSDACDownloader` to allow interrupted `.part` downloads to resume from their exact byte offset rather than restarting from zero.
   - Introduce exponential backoff retries on socket read timeouts during chunk streaming.
   - Conduct transfers with explicit per-granule verification gates before proceeding to subsequent items in the batch.

