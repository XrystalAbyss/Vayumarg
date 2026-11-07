# Vayumarg — Milestone F2.3R Baseline Audit & Database Identity Verification Report

**Date:** 01 November 2026  
**Status:** **AUDITED & INDEPENDENTLY VERIFIED**  
**Role:** Principal Scientific Data Auditor, PostgreSQL/PostGIS Architect, Python Infrastructure Engineer  
**Milestone:** F2.3R (Authentic Satellite Acquisition Reconciliation & Scientific Integrity)

---

## 1. Executive Summary

Milestone **F2.3R** was initiated to perform a forensic, evidence-driven verification of the claims submitted in Milestone F2.3. 
This audit independently inspected the actual repository, environment, physical files, and live PostgreSQL database. 
All baseline cryptographic checksums match bit-for-bit, and the database identity was clarified.

---

## 2. Environment & Database Identity Audit

### 2.1 The `vayumarg_dev` vs `vayumarg` Clarification
Earlier milestone reports occasionally referred to `vayumarg_dev` in text. Forensic inspection of `src/vayumarg/core/config.py`, `.env`, and the live PostgreSQL server on `127.0.0.1:5433` resolved this definitively:
- **Canonical PostgreSQL Database:** `vayumarg` (configured via `DATABASE_URL` in `src/vayumarg/core/config.py`).
- **Isolated Integration Test Database:** `vayumarg_test` (configured via `TEST_DATABASE_URL`).
- **Inspection of `pg_database`:**
  ```sql
  SELECT datname FROM pg_database WHERE datistemplate = false;
  -- Result: ['postgres', 'vayumarg', 'vayumarg_test']
  ```
- **Conclusion:** There is **no database named `vayumarg_dev`** on the server. The reference to `vayumarg_dev` in the F2.3 narrative was a documentation naming slip referring to the primary development/research database `vayumarg`. The database host is `127.0.0.1`, port is `5433`, migration head is `006_satellite_provenance`, and all test isolation safeguards remain functional.

---

## 3. Cryptographic Asset & Baseline Verification

Direct cryptographic re-hashing of physical assets confirmed complete foundation preservation:

| Target Entity | Physical Path | Expected SHA-256 | Computed SHA-256 | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| **Authentic Remal L1B Granule** | `data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | **MATCH (BIT-PERFECT)** |
| **Multichannel Processed Crop** | `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5` | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | **MATCH (BIT-PERFECT)** |
| **Frozen F1.1 Dataset Manifest**| `data/manifests/vayumarg_f1_1_freeze_manifest.json` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | **MATCH (BIT-PERFECT)** |

---

## 4. Live PostgreSQL Invariant Verification

Direct queries to `vayumarg` on `localhost:5433` confirmed exact preservation of all canonical tables:

| Table Name | Row Count | Invariant Status | Notes |
| :--- | :--- | :--- | :--- |
| `data_sources` | 1 | Preserved | NOAA IBTrACS v04r01 primary provider |
| `source_assets` | 1 | Preserved | NOAA CSV raw source asset |
| `ingestion_runs` | 2 | Preserved | Historical F1 & F1.1 ingestion runs |
| `storms` | 1,860 | Preserved | North Indian Ocean basin (1842–2024) |
| `track_observations` | 104,374 | Preserved | Dual-agency IMD (3-min) & JTWC (1-min) fixes |
| `data_quality_issues` | 8 | Preserved | Persisted reconciliation audit issues |
| `dataset_snapshots` | 1 | Preserved | F1.1 frozen snapshot record |
| `satellite_products` | 10 | Preserved | INSAT-3D/3DR/3DS and TCIR product registry |
| `satellite_granules` | 2 | Preserved | 1 `REAL_VERIFIED`, 1 `SYNTHETIC_FIXTURE` |
| `satellite_processed_crops` | 13 | Preserved | 1 `REAL_VERIFIED`, 12 `SYNTHETIC_FIXTURE` |
| `satellite_track_associations` | 23 | Preserved | 2 `REAL_VERIFIED`, 21 `SYNTHETIC_FIXTURE` |

---

## 5. Synthetic Fixture Quarantine Status

The 12 synthetic TCIR pilot crops and 21 synthetic track associations generated during milestone F2 were verified to remain strictly quarantined under `verification_status = 'SYNTHETIC_FIXTURE'`. 
The export contract [`export_module_a_multichannel_dataset`](file:///c:/Users/astra/Desktop/Project/Vayumarg/src/vayumarg/contracts/export.py) filters strictly on `REAL_VERIFIED`, guaranteeing zero synthetic leakage into machine-learning datasets.

