# VAYUMARG 3.0 — P1 SCIENTIFIC ASSET INVENTORY & CLASSIFICATION

**Audit Date:** 7 November 2026  
**Auditor:** Scientific Data Engineer & Research Reproducibility Auditor  
**Machine-Readable Inventory:** [`reports/v3/scientific_asset_inventory.json`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/v3/scientific_asset_inventory.json)  
**Total Scanned Project Files:** 3,215 files (excluding `.venv`, `.git`, `node_modules`, `.pytest_cache`)  

---

## 1. Executive Summary & Category Breakdown

Every physical file in `C:\Users\astra\Desktop\Project\Vayumarg` was scanned, measured, and classified according to scientific utility, reproducibility, licensing restrictions, and cloud backup eligibility:

| Category | File Count | Total Size (MB) | Recommended Primary Destination | Backup Eligibility | Reproducibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DATASET_RAW`** | 2,507 | 1,766.68 MB | Google Drive / Local Storage | **PENDING_LICENSE_REVIEW** (MOSDAC) / **ELIGIBLE** (NASA/IBTrACS) | Irreproducible Original |
| **`TEMPORARY`** | 3 | 349.12 MB | Local Purge Candidate | **EXCLUDED_CORRUPT** (Truncated `.part` files) | Reproducible / Disposable |
| **`MODEL_CHECKPOINT`** | 4 | 135.16 MB | Google Drive `03_Trained_Models` | **ELIGIBLE_FOR_BACKUP** | Computationally Expensive |
| **`DATABASE_BACKUP`** | 1 | 40.12 MB | Google Drive `06_Backups` | **ELIGIBLE_FOR_BACKUP** | Canonical Database State |
| **`UNKNOWN / MISC`** | 84 | 15.90 MB | Local / GitHub | **REVIEWED_NON_SENSITIVE** (Hackathon Docs/Tools) | Reproducible |
| **`DERIVED_VISUAL`** | 216 | 5.89 MB | Local Cache / Optional Drive | **EXCLUDED_DERIVATIVE** (Regenerable PNGs) | Regenerable from HDF5 |
| **`RESEARCH_REPORT`** | 129 | 4.87 MB | GitHub & Google Drive | **ELIGIBLE_FOR_BACKUP** | Unique Scientific Evidence |
| **`DATASET_MANIFEST`**| 12 | 3.78 MB | GitHub & Google Drive | **ELIGIBLE_FOR_BACKUP** | Authoritative Metadata |
| **`PUBLIC_DOCUMENTATION`**| 38 | 3.62 MB | GitHub & Google Drive | **ELIGIBLE_FOR_BACKUP** | User & Architecture Docs |
| **`SOURCE_CODE`** | 211 | 3.05 MB | GitHub (Canonical Source) | **ELIGIBLE_FOR_BACKUP** (Archival Snapshot) | Version Controlled |
| **`DATASET_PROCESSED`**| 5 | 2.59 MB | Google Drive `02_Scientific_Datasets`| **ELIGIBLE_FOR_BACKUP** | Calibrated HDF5 Crops |
| **`EXPERIMENT_LEDGER`**| 4 | 0.02 MB | GitHub & Google Drive | **ELIGIBLE_FOR_BACKUP** | Immutable Benchmark Metrics |
| **`SECRET_OR_PRIVATE`**| 1 | 0.00 MB | Local Developer Only | **EXCLUDED_SECRET** (`.env.example`) | Template Only |
| **TOTAL** | **3,215** | **2,330.80 MB** | — | — | — |

---

## 2. High-Value Scientific Assets Detail

### 2.1 Trained Model Checkpoints (`135.16 MB`, 4 files)
- `models/vayumarg/vision/satellite_cnn_best.pt` (129.16 MB, SHA-256: `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865`)
- `models/vayumarg/vision/satellite_convlstm_best.pt` (4.15 MB, SHA-256: `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d`)
- `models/vayumarg/track_gru_best.pt` (1.65 MB, SHA-256: `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986`)
- `models/vayumarg/track_hybrid_residual_best.pt` (0.20 MB, SHA-256: `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0`)

### 2.2 Calibrated Multi-Channel Scientific Crops (`2.59 MB`, 5 files)
- `data/processed/satellite/crops/AMPHAN_20200519_2358_MULTICHANNEL.h5` (1.93 MB)
- `data/processed/satellite/crops/BIPARJOY_20230612_2358_MULTICHANNEL.h5` (1.93 MB)
- `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5` (1.93 MB)
- `data/processed/satellite/crops/DANA_20241025_2330_MULTICHANNEL.h5` (1.93 MB)
- `data/processed/satellite/crops/REMAL_20240526_1802_TIR1.h5` (0.48 MB)

### 2.3 Curated Benchmark Manifests & Experiment Ledgers (`3.80 MB`, 16 files)
- `data/processed/satellite/nasa_cyclone/dataset_manifest.json` (1.43 MB)
- `data/processed/satellite/nasa_cyclone/sequences_manifest.json` (1.75 MB)
- `models/vayumarg/vision/cnn_evaluation_metrics.json` (4.8 KB)
- `models/vayumarg/vision/convlstm_evaluation_metrics.json` (3.8 KB)
- `models/vayumarg/vision/insat_cross_domain_evaluation.json` (7.0 KB)
- `models/vayumarg/track_gru_evaluation_metrics.json` (4.9 KB)

---

## 3. Exclusion Matrix & Rationale

1. **Truncated `.part` Downloads (349.12 MB, EXCLUDED):**
   - `data/raw/satellite/insat_real/3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5.part` (309.1 MB)
   - `data/raw/satellite/insat_real/3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5.part` (31.5 MB)
   - `data/raw/ibtracs_ni_v04r01.csv.part` (25.5 MB)
   - *Rationale:* Corrupted partial downloads that fail HDF5/CSV checksum validation. Uploading broken binaries wastes bandwidth and pollutes cloud storage.
2. **Python Virtual Environment (`.venv`, 4.84 GB, EXCLUDED):**
   - Contains 24,612 machine-specific pre-compiled DLLs and wheels. Fully reproducible via `uv.lock` and `pyproject.toml`.
3. **Derived Image Previews (5.89 MB, EXCLUDED):**
   - 216 pre-rendered PNGs in `data/processed/satellite/previews/` and `data/demo_cache/`. Regenerable on demand via `SatelliteVisualizer`.

---

## 4. Backup Volume Budget

- **Tier 1 (Safe Foundation Backup — Non-Sensitive Docs, Manifests & Checksum Ledgers):** **~12.5 MB** (Immediate Candidate upon OAuth consent).
- **Tier 2 (High-Value Checkpoints & Processed Crops):** **~138 MB** (Approval-ready).
- **Tier 3 (Database SQL Dump):** **~40 MB** (Approval-ready).
- **Tier 4 (NASA Training Images & NOAA IBTrACS):** **~70 MB** (Approval-ready).
- **Tier 5 (Raw ISRO MOSDAC Full-Disk Granules):** **~1,725 MB** (Quarantined pending owner data-governance review).
- **Total Safe Approved Backup Volume (Tiers 1–4):** **~260 MB**.

