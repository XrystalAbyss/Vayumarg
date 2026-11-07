# VAYUMARG 3.0 — P1-DRIVE.2 SCIENTIFIC INVENTORY RECONCILIATION REPORT

**Audit Date:** 7 November 2026, 16:15 IST  
**Auditor:** Senior Scientific Data Engineer & Systems Integration Auditor  
**Local Workspace:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Status:** **RECONCILED (ZERO DISCREPANCY, EXACT BYTE ACCOUNTING)**  

---

## 1. Investigation of the Inventory Discrepancy

In the P1-DRIVE.1 summary, a numerical gap emerged between the high-level scanner output and the rendered markdown category summary:

- **Claimed Total Scanned:** 3,215 files | 2,330.80 MB
- **Displayed Category Table Sum:** 2,872 files | 2,305.37 MB
- **Apparent Unexplained Discrepancy:** 343 files | 25.43 MB

### Root Cause Analysis
An exhaustive file-level query of [`reports/v3/scientific_asset_inventory.json`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/v3/scientific_asset_inventory.json) revealed that **all 3,215 files were captured**, but the markdown table presented an abbreviated rollup that omitted five specific classification categories:

1. `DERIVED_VISUAL`: 216 files | 5.89 MiB (6,173,596 bytes)
2. `UNKNOWN`: 84 files | 15.90 MiB (16,668,774 bytes)
3. `PUBLIC_DOCUMENTATION`: 38 files | 3.62 MiB (3,797,840 bytes)
4. `EXPERIMENT_LEDGER`: 4 files | 0.02 MiB (20,496 bytes)
5. `SECRET_OR_PRIVATE`: 1 file | 0.0007 MiB (786 bytes, `.env`)

$$\text{Omitted Files} = 216 + 84 + 38 + 4 + 1 = 343\text{ files}$$
$$\text{Omitted Volume} = 5.8876 + 15.8966 + 3.6219 + 0.0195 + 0.0007 = 25.43\text{ MiB}$$
$$\text{Total Files} = 2,872 + 343 = 3,215\text{ files}$$
$$\text{Total Volume} = 2,305.37\text{ MiB} + 25.43\text{ MiB} = 2,330.80\text{ MiB}$$

The discrepancy is 100% mathematically accounted for.

---

## 2. Unit Clarification: Decimal MB vs. Binary MiB

A secondary source of confusion in previous audit notes was the colloquial use of the "MB" symbol for binary mebibytes ($2^{20} = 1,048,576\text{ bytes}$). The canonical local disk inventory is:

$$\text{Exact Byte Count} = 2,444,023,823\text{ bytes}$$
$$\text{Binary Mebibytes (MiB)} = \frac{2,444,023,823}{1,048,576} = 2,330.80\text{ MiB}$$
$$\text{Decimal Megabytes (MB)} = \frac{2,444,023,823}{1,000,000} = 2,444.02\text{ MB}$$
$$\text{Binary Gibibytes (GiB)} = \frac{2,444,023,823}{1,073,741,824} = 2.276\text{ GiB}$$

All tables hereafter report both Binary MiB and Decimal MB to avoid ambiguity.

---

## 3. Comprehensive Reconciled Category Ledger

Every one of the 3,215 files belongs to exactly one primary category:

| Primary Category | File Count | Binary Size (MiB) | Decimal Size (MB) | Exact Bytes | Backup Disposition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DATASET_RAW`** | 2,507 | 1,766.68 MiB | 1,852.49 MB | 1,852,493,364 | Retain locally; Tier 3 Cloud Archive |
| **`TEMPORARY`** | 3 | 349.12 MiB | 366.08 MB | 366,084,096 | **EXCLUDED (Incomplete `.part` files)** |
| **`MODEL_CHECKPOINT`** | 4 | 135.16 MiB | 141.73 MB | 141,726,361 | Priority Tier 2 Cloud Transfer |
| **`DATABASE_BACKUP`** | 1 | 40.12 MiB | 42.07 MB | 42,071,784 | Priority Tier 2 Cloud Transfer |
| **`UNKNOWN`** | 84 | 15.90 MiB | 16.67 MB | 16,668,774 | Audit & Classify (zips, interim h5, config) |
| **`DERIVED_VISUAL`** | 216 | 5.89 MiB | 6.17 MB | 6,173,596 | UI previews; reproducible from raw |
| **`RESEARCH_REPORT`** | 129 | 4.87 MiB | 5.10 MB | 5,104,618 | Tier 1 Synchronized / Git Docs |
| **`DATASET_MANIFEST`** | 12 | 3.78 MiB | 3.96 MB | 3,961,075 | Tier 1 Synchronized / Git Tracking |
| **`PUBLIC_DOCUMENTATION`** | 38 | 3.62 MiB | 3.80 MB | 3,797,840 | Git Tracking (`docs/`, `README.md`) |
| **`SOURCE_CODE`** | 211 | 3.05 MiB | 3.20 MB | 3,202,169 | Core Git repository (`src/`, `frontend/src`) |
| **`DATASET_PROCESSED`** | 5 | 2.59 MiB | 2.72 MB | 2,718,864 | Tier 2 Cloud Transfer (HDF5 crops) |
| **`EXPERIMENT_LEDGER`** | 4 | 0.02 MiB | 0.02 MB | 20,496 | Git Tracking / Tier 1 Drive |
| **`SECRET_OR_PRIVATE`** | 1 | 0.0007 MiB | 0.0008 MB | 786 | **STRICTLY LOCAL (`.env` — EXCLUDED)** |
| **TOTAL** | **3,215** | **2,330.80 MiB** | **2,444.02 MB** | **2,444,023,823** | **100% RECONCILED** |

---

## 4. Deep-Dive on Critical Scientific Assets

### 4.1. Complete MOSDAC HDF5 Granules vs. Incomplete Downloads
The inventory contains **6 complete ISRO MOSDAC HDF5 granules** totaling 1,698.12 MiB (1,780,606,269 bytes):
1. `3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5`: 303,911,822 B (FANI)
2. `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5`: 302,500,294 B (AMPHAN)
3. `3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5`: 301,621,093 B (TAUKTAE)
4. `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5`: 303,022,442 B (BIPARJOY)
5. `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`: 294,275,518 B (REMAL)
6. `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5`: 275,275,100 B (DANA)

In addition, **3 incomplete `.part` files** were isolated in `TEMPORARY`:
1. `data/raw/ibtracs_ni_v04r01.csv.part`: 25,493,504 B
2. `data/raw/satellite/insat_real/3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5.part`: 31,457,280 B
3. `data/raw/satellite/insat_real/3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5.part`: 309,133,312 B

> [!IMPORTANT]
> The three `.part` files are interrupted download buffers and are marked `EXCLUDED` from all cloud backups and repository commits.

### 4.2. Raw NASA Training Dataset
- **Location:** `data/raw/satellite/nasa_cyclone/images/`
- **File Count:** Exactly 2,500 JPEG images across 25 storm IDs.
- **Physical Volume:** 45,291,595 bytes (43.19 MiB / 45.29 MB).
- **Integrity:** 100% physically readable and validated.

---

## 5. Excluded Scopes & Boundary Validation
- `.venv/` (Python virtual environment with 12,000+ files and multi-GB PyTorch/CUDA binaries) is excluded.
- `.git/` (local Git metadata) is excluded from the filesystem file scan.
- `frontend/node_modules/` is excluded; project is reproducible via `package.json` + `npm install`.
- No source datasets or model checkpoints were altered, overwritten, or moved during this reconciliation audit.

