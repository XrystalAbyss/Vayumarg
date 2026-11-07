# Vayumarg F2.4 Gate C Batch 1 — Download & Acquisition Execution Report

**Date:** 2026-11-01  
**Milestone:** F2.4 Gate C — Controlled Multi-Storm Satellite Acquisition  
**Phase:** Gate C Batch 1 Execution  
**Status:** **ACQUISITION SUCCESSFUL**  

---

## 1. Executive Summary

Under explicit owner authorization for **Gate C Batch 1**, the Vayumarg resilient acquisition engine executed the sequential download of two authorized authentic INSAT-3DR L1B satellite granules from the Space Applications Centre (SAC / ISRO) MOSDAC repository:
1. **Granule A — AMPHAN (2020):** Super Cyclonic Storm / Extremely Severe Cyclonic Storm anchor in the Bay of Bengal.
2. **Granule B — BIPARJOY (2023):** Very Severe Cyclonic Storm anchor in the Arabian Sea.

Both acquisitions succeeded on their first attempt without socket drops, premature EOFs, or HTTP range retries. Both files underwent strict pre-promotion structural validation (HDF5 root group inspection, dataset inventory verification, and checksum generation) before atomic promotion to the primary repository. Total network transfer was kept strictly within the pre-authorized 1.0 GB ceiling.

---

## 2. Authorized vs Actual Acquisition Inventory

| Parameter | Granule A — AMPHAN (2020) | Granule B — BIPARJOY (2023) | Batch 1 Total / Limit |
|---|---|---|---|
| **Cyclone Name** | AMPHAN | BIPARJOY | 2 Cyclones |
| **Ocean Basin** | Bay of Bengal (NIO) | Arabian Sea (AS) | 2 Distinct Basins |
| **Satellite** | INSAT-3DR | INSAT-3DR | Homogeneous Sensor Line |
| **Product Level** | `3RIMG_L1B_STD` | `3RIMG_L1B_STD` | Standard Imager L1B |
| **MOSDAC gId** | `8353650` | `11789302` | Registered MOSDAC assets |
| **Nominal Timestamp** | `2020-05-19 23:58 UTC` | `2023-06-12 23:58 UTC` | Synoptic matching 00:00 UTC |
| **Target Filename** | `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5` | `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5` | Conforming HDF5 |
| **Pre-Probed Size** | 302,500,294 bytes | 303,022,442 bytes | 605,522,736 bytes |
| **Actual Bytes Transferred** | **302,500,294 bytes** | **303,022,442 bytes** | **605,522,736 bytes** |
| **Network Budget Ceiling** | — | — | **1,000,000,000 bytes (1.0 GB)** |
| **Budget Utilization** | — | — | **60.55% (394.48 MB head-room)** |
| **Transfer Time** | 139.7 seconds | 123.6 seconds | 263.3 seconds (~4.4 min) |
| **Mean Throughput** | 2.16 MB/s | 2.45 MB/s | 2.30 MB/s average |
| **Socket Connection Attempts**| 1 (Zero drops) | 1 (Zero drops) | Single-pass streaming |
| **HDF5 Root Keys Count** | 36 keys | 36 keys | 100% Structural Parity |
| **SHA-256 Digest** | `032cde43fbd6741fd85e86e118144f63137c60f7ce023555cdf04ac38a3f0abb` | `b2f15cae5139468e2bac1804fd25138bff402b266c7939a7f2cd91a4b5a15220` | Cryptographically Verified |
| **Promotion State** | Promoted from `.part` | Promoted from `.part` | **ATOMICALLY VERIFIED** |

---

## 3. Network Execution & Socket Behavior

Prior to triggering full payloads, remote byte boundaries and HTTP `Range: bytes=0-1023` capabilities were probed via `scripts/probe_gate_c_candidates.py`. The MOSDAC server returned:
- `HTTP/1.1 206 Partial Content`
- `Accept-Ranges: bytes`
- `Content-Range: bytes 0-1023/302500294` (AMPHAN)
- `Content-Range: bytes 0-1023/303022442` (BIPARJOY)

During full acquisition via `scripts/execute_gate_c_batch_1.py`:
- Sequential transfers were strictly maintained: AMPHAN began and completed prior to BIPARJOY initialization.
- Streaming buffers of 256 KB were utilized.
- No TCP resets, HTTP 503, or connection timeouts occurred.
- File integrity checks via `h5py.File(part_file, "r")` verified the header, dataset trees (`IMG_TIR1`, `IMG_TIR2`, `IMG_MIR`, `IMG_WV`, etc.), and calibration lookups before renaming `.part` to `.h5`.

---

## 4. Local Storage Integrity

The files reside in the verified authentic storage directory:
- `data/raw/satellite/insat_real/3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5`
- `data/raw/satellite/insat_real/3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5`

No intermediate or `.part` files remain in the workspace. Disk space on `C:` remains healthy (~58.0 GB free).
