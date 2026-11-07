# Vayumarg F2.4 Gate D1 — Scientific Baseline & Storage Verification Report

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate D1 — Balanced Acquisition Selection & First-Batch Preflight  
**Auditor:** Principal Scientific Data Architect, PostgreSQL/PostGIS Engineer, QA Lead  
**Audit Scope:** Independent Verification of Reported Baseline Claims, Checksums, and System State  
**Baseline Status:** **INDEPENDENTLY VERIFIED & PRESERVED**  

---

## 1. Executive Summary

Prior to proposing any acquisition or modifying configuration manifests, an independent verification of Vayumarg's data repository, database instances, and raw assets was conducted. All baseline claims reported in Gate C1R were confirmed against actual file bytes on disk and PostgreSQL 16 relational tables.

---

## 2. Infrastructure & Environment Integrity

| Parameter | Configured Value / Path | Verified State | Audit Status |
|---|---|---|---|
| **Canonical Research Database** | `postgresql+psycopg://...:5433/vayumarg` | Operational & Healthy | **PASS** |
| **Integration Test Database** | `postgresql+psycopg://...:5433/vayumarg_test` | Isolated & Dedicated | **PASS** |
| **Current Alembic Revision** | `006_satellite_provenance` | Active on `vayumarg` | **PASS** |
| **Target Storage Volume** | Drive `C:` | **49.13 GB free** (475.67 GB total) | **PASS** |
| **Historical Baseline Storms** | Table `storms` | **1,860** canonical storms | **PASS** |
| **Historical Observations** | Table `track_observations` | **104,374** observations | **PASS** |
| **F1.1 Frozen Manifest SHA-256** | `vayumarg_f1_1_freeze_manifest.json` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | **PASS** |
| **DatasetSnapshot Invariant** | Table `dataset_snapshots` | Exact hash match | **PASS** |

---

## 3. Cryptographic Re-Verification of Existing Authentic Assets

All four previously acquired raw HDF5 granules and their corresponding standardized $201 \times 201$ multichannel crops were re-hashed from byte zero:

```
+-----------------------------------------------------------------------------------------------------------------------------------------+
| CYCLONE REMAL (2024) — INSAT-3DR L1B (gId 13745265)                                                                                     |
|   Raw HDF5:  data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5 (294,275,518 bytes)                                  |
|              SHA-256: 5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807                                                |
|   Crop HDF5: data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5 (633,554 bytes)                                        |
|              SHA-256: 7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90                                                |
+-----------------------------------------------------------------------------------------------------------------------------------------+
| CYCLONE DANA (2024) — INSAT-3DS L1B (gId 14514765)                                                                                      |
|   Raw HDF5:  data/raw/satellite/insat_real/3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5 (275,275,100 bytes)                                  |
|              SHA-256: 98f3e5640bbc8c1d42da0fd090c0b93ead2d239718946ce69c25d59921ad4fcf                                                |
|   Crop HDF5: data/processed/satellite/crops/DANA_20241025_2330_MULTICHANNEL.h5 (683,336 bytes)                                         |
|              SHA-256: 71915613322d06949b43b6a6343359fad58c5e8c82603216ef4229efc12b9463                                                |
+-----------------------------------------------------------------------------------------------------------------------------------------+
| CYCLONE AMPHAN (2020) — INSAT-3DR L1B (gId 8353650)                                                                                     |
|   Raw HDF5:  data/raw/satellite/insat_real/3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5 (302,500,294 bytes)                                  |
|              SHA-256: 032cde43fbd6741fd85e86e118144f63137c60f7ce023555cdf04ac38a3f0abb                                                |
|   Crop HDF5: data/processed/satellite/crops/AMPHAN_20200519_2358_MULTICHANNEL.h5 (602,279 bytes)                                       |
|              SHA-256: 86a14fcb9109c32cf6955bc7739202b9a86d08928a6df1ee503e3ba9a3e28b12                                                |
+-----------------------------------------------------------------------------------------------------------------------------------------+
| CYCLONE BIPARJOY (2023) — INSAT-3DR L1B (gId 11789302)                                                                                  |
|   Raw HDF5:  data/raw/satellite/insat_real/3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5 (303,022,442 bytes)                                  |
|              SHA-256: b2f15cae5139468e2bac1804fd25138bff402b266c7939a7f2cd91a4b5a15220                                                |
|   Crop HDF5: data/processed/satellite/crops/BIPARJOY_20230612_2358_MULTICHANNEL.h5 (697,937 bytes)                                       |
|              SHA-256: a4ce1ee39cb21cc016fb7d2cd929d775f31773ef4813d8cfc351f60cac1a835c                                                |
+-----------------------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. PostgreSQL Relational State & Quarantine Audit

- **`satellite_granules`:** 4 `REAL_VERIFIED`, 1 `SYNTHETIC_FIXTURE` (quarantined).
- **`satellite_processed_crops`:** 4 `REAL_VERIFIED`, 12 `SYNTHETIC_FIXTURE` (quarantined).
- **`satellite_track_associations`:** 10 `REAL_VERIFIED` (3 IMD, 4 JTWC, 3 IBTrACS), 21 `SYNTHETIC_FIXTURE` (quarantined).
- **Automated Test Baseline:** **109 passed in 64.63s**; `ruff check` and `ruff format` clean.
- **Git State:** 0 commits, 0 pushes, 0 branch modifications.

