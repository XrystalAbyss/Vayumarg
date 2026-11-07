# Milestone F2.4: Baseline Verification Audit

**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Milestone:** F2.4 — Scientific Integrity Closure, Fault-Tolerant MOSDAC Recovery and Controlled Authentic Satellite Dataset Expansion  
**Audit Timestamp:** 2026-11-01T22:25:00+05:30  
**Audit Author:** Principal Satellite Data Engineer & Scientific QA Lead  

---

## 1. Cryptographic Baseline Verification

All core repository assets and reference manifests were audited directly against physical storage:

| Asset Description | File Path | Expected SHA-256 | Actual Computed SHA-256 | Status |
|:---|:---|:---|:---|:---|
| **F1.1 Frozen Dataset Manifest** | `data/manifests/vayumarg_f1_1_freeze_manifest.json` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | **MATCH (BIT-PERFECT)** |
| **Authentic Remal L1B HDF5** | `data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | **MATCH (BIT-PERFECT)** |
| **Authentic Remal Multichannel Crop** | `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5` | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | **MATCH (BIT-PERFECT)** |
| **Authentic Remal TIR1 Single Crop** | `data/processed/satellite/crops/REMAL_20240526_1802_TIR1.h5` | `036b84007e9ab8395e8466d3b27c832ee0ac2a81e4e9b216117548959932fd9f` | `036b84007e9ab8395e8466d3b27c832ee0ac2a81e4e9b216117548959932fd9f` | **MATCH (BIT-PERFECT)** |

---

## 2. PostgreSQL Relational State Baseline

Live inspection of PostgreSQL 16.4 on port 5433 confirmed runtime database naming and exact row counts:

- **Canonical Research Database:** `vayumarg` (verified via `psycopg` connection).
- **Isolated Integration Test Database:** `vayumarg_test`.
- **Database Table Structure:**
  - `storms`: **1,860** rows (100% authentic NOAA IBTrACS).
  - `track_observations`: **104,374** rows (100% authentic NOAA IBTrACS).
  - `satellite_products`: **10** rows (2 authentic INSAT products: `3RIMG_L1B_STD`, `3SIMG_L1B_STD`; 8 synthetic fixtures).
  - `satellite_granules`: **2** rows (1 authentic Remal L1B granule; 1 synthetic fixture `TCIR_NIO_PILOT_2020_2023`).
  - `satellite_processed_crops`: **13** rows (1 authentic Remal 201x201 crop; 12 synthetic fixtures).
  - `satellite_track_associations`: **23** rows (2 authentic associations for Remal [1 IMD primary + 1 JTWC secondary]; 21 synthetic fixtures).
  - `source_assets`: **1** row (IBTrACS authentic CSV asset).
  - `dataset_snapshots`: **1** row (F1.1 frozen snapshot).
  - `storm_aliases`: **2,534** rows.

---

## 3. Physical Storage & Environment Baseline

- **Drive C Free Space:** 59.48 GB (Available for bounded Option A acquisition; MK11 directory untouched).
- **Python Environment:** Python 3.12.10 virtual environment (`.venv`).
- **Test Baseline:** 79 unit/integration tests passing.
- **Git Working Tree:** Clean, untracked working files, 0 commits, 0 branch divergence.

