# Vayumarg F2.4 Gate C1R — Baseline Preservation & Source Identity Audit

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate C1R — Scientific Metadata Closure & Gate D Preflight  
**Auditor:** Principal Scientific Data Architect, PostgreSQL/PostGIS Integrity Auditor, QA Lead  
**Audit Status:** **BASELINE INDEPENDENTLY VERIFIED & PRESERVED**  

---

## 1. Executive Summary

Milestone **F2.4 Gate C1R** performed an exhaustive, independent verification of Vayumarg's data infrastructure across the PostgreSQL research database `vayumarg`, isolated test database `vayumarg_test`, local file repositories, raw HDF5 assets, processed crops, and historical baseline snapshots.

All baseline assets, cryptographic checksums, database relationships, and provenance boundaries were audited and found to be in an intact, non-corrupted state.

---

## 2. Comprehensive Asset & Checksum Audit

### 2.1 Authentic Raw Satellite Granules (`data/raw/satellite/insat_real/`)

| Cyclone | Satellite / Sensor | Product Level | MOSDAC gId | Nominal Acquisition (UTC) | Exact File Size (Bytes) | SHA-256 Digest |
|---|---|---|---|---|---|---|
| **REMAL** | INSAT-3DR IMAGER | `3RIMG_L1B_STD` | `13745265` | `2024-05-26 18:02:00` | 294,275,518 | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` |
| **DANA** | INSAT-3DS IMAGER | `3SIMG_L1B_STD` | `14514765` | `2024-10-25 23:30:00` | 275,275,100 | `98f3e5640bbc8c1d42da0fd090c0b93ead2d239718946ce69c25d59921ad4fcf` |
| **AMPHAN** | INSAT-3DR IMAGER | `3RIMG_L1B_STD` | `8353650` | `2020-05-19 23:58:00` | 302,500,294 | `032cde43fbd6741fd85e86e118144f63137c60f7ce023555cdf04ac38a3f0abb` |
| **BIPARJOY**| INSAT-3DR IMAGER | `3RIMG_L1B_STD` | `11789302` | `2023-06-12 23:58:00` | 303,022,442 | `b2f15cae5139468e2bac1804fd25138bff402b266c7939a7f2cd91a4b5a15220` |

### 2.2 Processed Multichannel Crops (`data/processed/satellite/crops/`)

| Cyclone | Target Grid & Channels | File Size (Bytes) | SHA-256 Digest | PostgreSQL Crop UUID |
|---|---|---|---|---|
| **REMAL** | $201 \times 201$ (TIR1, WV, TIR2, MIR) | 633,554 | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | `e93002d6-a5e2-4ae2-8adf-fa7a50d0da36` |
| **DANA** | $201 \times 201$ (TIR1, WV, TIR2, MIR) | 678,924 | `71915613322d06949b43b6a6343359fad58c5e8c82603216ef4229efc12b9463` | `869cd46b-659a-430a-8a45-d2fd8ad7174b` |
| **AMPHAN** | $201 \times 201$ (TIR1, WV, TIR2, MIR) | 602,279 | `86a14fcb9109c32cf6955bc7739202b9a86d08928a6df1ee503e3ba9a3e28b12` | `142da9e9-417e-428b-acba-b68e3aab0199` |
| **BIPARJOY**| $201 \times 201$ (TIR1, WV, TIR2, MIR) | 697,937 | `a4ce1ee39cb21cc016fb7d2cd929d775f31773ef4813d8cfc351f60cac1a835c` | `fc074478-42dd-4d02-b86f-8eb109cc9872` |

---

## 3. Database State & Historical Invariants

### 3.1 Migration Revision & Schema Safety
- **Current Alembic Revision:** `006_satellite_provenance` (enforcing column `verification_status` and data isolation).
- **PostgreSQL Connection:** Canonical URL `postgresql+psycopg://vayumarg_user:***@127.0.0.1:5433/vayumarg`.
- **Foreign Key Cascade Integrity:** All `SatelliteProcessedCrop` records reference valid `Storm` and `SatelliteGranule` foreign keys. All `SatelliteTrackAssociation` records reference valid `SatelliteProcessedCrop` and `TrackObservation` foreign keys.

### 3.2 Historical Baseline Preservation
- **Module B Benchmark Storm Count:** Exactly **1,860** storms in table `storms`.
- **Module B Benchmark Track Observations:** Exactly **104,374** records in table `track_observations`.
- **Frozen Manifest Hash:** `data/manifests/vayumarg_f1_1_freeze_manifest.json` has exact SHA-256 `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`.
- **Database Snapshot Entry:** Table `dataset_snapshots` holds the record matching this exact hash. Invariant count: 0 unintended mutations.

### 3.3 Synthetic Fixture Isolation
- Table `satellite_granules`: 4 `REAL_VERIFIED`, 1 `SYNTHETIC_FIXTURE` (quarantined).
- Table `satellite_processed_crops`: 4 `REAL_VERIFIED`, 12 `SYNTHETIC_FIXTURE` (quarantined).
- Table `satellite_track_associations`: 10 `REAL_VERIFIED`, 21 `SYNTHETIC_FIXTURE` (quarantined).
- All queries filtering `verification_status = 'REAL_VERIFIED'` remain 100% immune to synthetic data contamination.

