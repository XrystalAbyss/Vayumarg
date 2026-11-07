# F2.1 TCIR Pilot Source Provenance Audit & Resolution Report

**Milestone:** F2.1  
**Date:** 2026-11-01  
**Project:** Vayumarg — Scientific Data Foundation (Team VortexA / SIH 2026 / CV-IP)  
**Auditor:** Principal Remote-Sensing Specialist & Scientific Integrity Reviewer  

---

## 1. Executive Summary & Problem Formulation

During the review of Milestone F2, an investigation into the interim pilot dataset `data/interim/tcir_nio_pilot.h5` and its corresponding database entries was conducted.

The published, peer-reviewed Tropical Cyclone Image Routing (TCIR) dataset (Chen, Chen & Lin, 2018; NTU CSIE) spans the historical period **2003 through 2017**. However, the F2 pilot dataset contained 12 satellite frames attributed to:
- **Cyclone AMPHAN (May 2020)** — 6 frames
- **Cyclone BIPARJOY (June 2023)** — 6 frames

This created an apparent scientific contradiction: how could cyclones from 2020 and 2023 exist inside an authentic 2003–2017 historical TCIR archive?

---

## 2. Forensic Code & Artifact Audit

Inspection of `scripts/generate_tcir_pilot.py` revealed:
1. **Algorithmic Simulation:**
   The file `data/interim/tcir_nio_pilot.h5` was generated locally using NumPy Gaussian cloud-top temperature models (`np.random.seed(42)`). Cold convective cores (190–310 K) and water vapor signatures were mathematically generated on a $201 \times 201 \times 4$ tensor.
2. **Metadata Hybridization:**
   The frame metadata (`info` table) drew real storm timestamps, coordinates, and intensity estimates from NOAA IBTrACS for AMPHAN and BIPARJOY, but paired them with simulated synthetic raster arrays to serve as an engineering test fixture for format compliance and alignment profiling.
3. **Scientific Integrity Risk:**
   In F2, these frames were ingested into `satellite_granules`, `satellite_processed_crops`, and `satellite_track_associations` without an explicit metadata flag distinguishing synthetic test fixtures from authentic sensor observations. If downstream ML researchers consumed these tables, synthetic images would have leaked into real convolutional neural network training pipelines.

---

## 3. Structural Remediation & Forward Migration

To resolve this issue with permanent database-level guarantees:

### 3.1 Migration 006 (`006_satellite_provenance.py`)
Alembic migration 006 was created and applied:
- Added `verification_status` column (`VARCHAR(50)`, default `'PROVENANCE_UNVERIFIED'`) to:
  - `satellite_granules`
  - `satellite_processed_crops`
  - `satellite_track_associations`
- **Data Migration:**
  All existing records originating from `TCIR_NIO_PILOT` were retroactively updated from default to `'SYNTHETIC_FIXTURE'`:
  - Granules updated: 1 (`TCIR_NIO_PILOT_2020_2023`)
  - Processed crops updated: 12 (all marked `SYNTHETIC_FIXTURE`)
  - Track associations updated: 21 (all marked `SYNTHETIC_FIXTURE`)

### 3.2 Strict Export Contract Enforcement
In `src/vayumarg/contracts/export.py`, the new export contract `export_satellite_paired_dataset(...)` strictly enforces `verification_status == 'REAL_VERIFIED'` by default.

**Verification Test Result:**
- When queried for `verification_status="REAL_VERIFIED"`: **0 records** returned.
- When queried for `verification_status="SYNTHETIC_FIXTURE"`: **21 records** returned.

Synthetic fixtures are now cleanly segregated and cannot contaminate operational ML training.

---

## 4. TCIR Historical Archive Acquisition Plan

For genuine historical TCIR coverage (2003–2017):
- Authentic source: NTU CSIE TCIR repository (`http://tcir.csie.ntu.edu.tw/` / GitHub / academic mirrors).
- Authentic files follow the naming `TCIR-ALL_*.h5` containing true GridSat-B1 and CMORPH merged multi-satellite observations.
- When ingested in future data pipelines, genuine TCIR frames will be flagged as `REAL_VERIFIED` after verifying their SHA-256 against published academic checksums.

