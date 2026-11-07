# Milestone F2.4 — Gate C Baseline Verification Report

## Executive Summary

Prior to initiating any multi-storm batch planning or acquisition under Milestone F2.4 Gate C, the physical, relational, and cryptographic baseline of the Vayumarg repository was independently re-verified against the active filesystem and PostgreSQL databases (`vayumarg` and `vayumarg_test`).

All 11 Gate B acceptance criteria have been verified with bitwise and relational precision:
1. **Total Authentic Source Granules:** Exactly two completed, valid INSAT L1B HDF5 granules on disk and registered in `satellite_granules` (`REAL_VERIFIED`).
2. **Total Authentic Multichannel Crops:** Exactly two physical crops on disk (`data/processed/satellite/crops/`) registered in `satellite_processed_crops` (`REAL_VERIFIED`).
3. **Historical Data Foundation:** NOAA IBTrACS historical database remains perfectly frozen with 1,860 storms and 104,374 observations.
4. **Synthetic Quarantine:** Synthetic TCIR fixture data remains strictly isolated under `SYNTHETIC_FIXTURE` governance status.
5. **Software Test Suite:** 96 automated tests passing across unit and integration suites (baseline of 91 preserved and expanded to 96 with zero regressions).

---

## 1. Physical Source Granule Inventory

| Granule Filename | Mission | Sensor | Exact Size (Bytes) | Cryptographic SHA-256 | Verification Status | PostgreSQL UUID |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` | INSAT-3DR | IMAGER | 294,275,518 | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | `REAL_VERIFIED` | `d4bdb439-76ec-4c83-b974-318e27c4dd43` |
| `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5` | INSAT-3DS | IMAGER | 275,275,100 | `98f3e5640bbc8c1d42da0fd090c0b93ead2d239718946ce69c25d59921ad4fcf` | `REAL_VERIFIED` | `5b5d4dc5-9e4d-4745-af98-a49cf9377a09` |

### Audit of Partial Files on Disk
- `3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5.part`: 31,457,280 bytes. Quarantined partial file from F2.3 aborted run; not registered in PostgreSQL and not promoted.
- Zero other `.part` files exist in `data/raw/satellite/insat_real/`.

---

## 2. Processed Multichannel Crops & Associations

| Crop URI | Target Storm | Center (Lat, Lon) | Extent | Target Grid | SHA-256 Checksum | Associations | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5` | REMAL (2024) | 21.70°N, 89.20°E | 800 km | 201×201 | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | IMD (dt=2m, dr=1.03km)<br>JTWC (dt=2m, dr=91.94km) | `REAL_VERIFIED` |
| `data/processed/satellite/crops/DANA_20241025_2330_MULTICHANNEL.h5` | DANA (2024) | 21.20°N, 86.40°E | 800 km | 201×201 | `71915613322d06949b43b6a6343359fad58c5e8c82603216ef4229efc12b9463` | JTWC (dt=30m, dr=0.00km)<br>IBTRACS (dt=30m, dr=0.00km) | `REAL_VERIFIED` |

---

## 3. Scientific Invariant Verification

1. **NOAA IBTrACS Historical Dataset Freeze:**
   - Canonical Database: PostgreSQL `vayumarg` (port 5433).
   - Storm Records: Exactly 1,860 rows.
   - Track Observation Records: Exactly 104,374 rows.
   - F1.1 Dataset Snapshot Record: `vayumarg-nio-ibtracs-f1.1-freeze` with bit-perfect SHA-256 `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`.
2. **Synthetic Quarantine:**
   - 1 Synthetic Granule (`TCIR_NIO_PILOT_2020_2023`), 12 Synthetic Crops, 21 Synthetic Associations remain strictly labeled `SYNTHETIC_FIXTURE`.
   - Zero synthetic rows are linked to real satellite granules or historical track observations.
3. **Database Migration State:**
   - Database schema is at migration head `006_synthetic_provenance_isolation`.
   - Production (`vayumarg`) and test (`vayumarg_test`) database isolation is confirmed.

---

## 4. Test Suite Baseline

- Automated test suite executed via `pytest`:
  - **96 passed** (zero failed, zero warnings, zero skipped).
  - Test execution duration: ~25 seconds.
  - Codebase linting and formatting audited with `ruff`: clean (zero errors).

