# F2.1 Baseline Audit Report: Environment, Pre-Conditions, and Data State

**Milestone:** F2.1 (Secure MOSDAC Authentication, Real INSAT Acquisition, TCIR Provenance Audit and Scientific Integration)  
**Date:** 2026-11-01  
**Project:** Vayumarg (SIH 2026 / CV-IP, Problem Statement SIH26070, Team VortexA)  
**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Auditor:** Principal Satellite Data Engineer & Independent Quality Lead  

---

## 1. Executive Summary

Prior to beginning Milestone F2.1 implementation, a comprehensive non-destructive inspection of the Vayumarg repository, PostgreSQL 16.4 / PostGIS 3.4.3 database, test baseline, and physical storage was executed.

All pre-conditions for F2.1 are verified and healthy:
- **Operating System:** Windows 11 Home Single Language (Build 26100), PowerShell shell.
- **Python Runtime:** Python 3.12.10 (`.venv\Scripts\python.exe`), managed via `uv`.
- **Database Engine:** PostgreSQL 16.4 (Debian 16.4-1.pgdg120+1) with PostGIS 3.4.3 on `localhost:5433` (Docker Compose container `vayumarg-db-postgis`).
- **Current Alembic Revision:** `005_satellite_data_foundation` (head).
- **Existing Test Suite:** **53/53 passed** in 14.16 seconds.
- **Git Working Tree:** Clean, untracked development branch, zero commits per project owner deferral constraint until 2 November 2026.
- **Free Disk Space:** 179 GB available on drive `C:`, well exceeding the minimum requirement (> 20 GB).
- **F1.1 Scientific Freeze Manifest:** Checksum `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` matches database snapshot `c36a218a-09db-4bec-a02f-da546b83df02` with 104,374 samples.

---

## 2. Table-by-Table Database Inventory

Verification of production research database `vayumarg`:

| Table Name | Record Count | Notes / Status |
|:---|:---|:---|
| `data_sources` | 1 | Official NOAA NCEI IBTrACS |
| `source_assets` | 1 | `ibtracs.NI.list.v04r01.csv` raw source |
| `ingestion_runs` | 2 | F1 initial ingestion and F1.1 reconciliation |
| `storms` | 1,860 | Canonical NIO storms |
| `storm_aliases` | 2,534 | Cross-agency aliases (IMD, JTWC, WMO) |
| `track_observations` | 104,374 | Validated 3-min/1-min/10-min observations |
| `data_quality_issues` | 8 | Persisted audit findings |
| `dataset_snapshots` | 1 | Freeze `vayumarg-nio-ibtracs-f1.1-freeze` |
| `satellite_products` | 1 | Initial product `TCIR_NIO_PILOT` |
| `satellite_granules` | 1 | Pilot granule `TCIR_NIO_PILOT_2020_2023` |
| `satellite_processed_crops` | 12 | Initial pilot frames (Subject to Provenance Audit in Phase B) |
| `satellite_track_associations` | 21 | Initial pilot associations (Subject to Provenance Audit in Phase B) |

---

## 3. Discrepancy & Provenance Risk Highlight

A critical finding identified prior to F2.1 requires immediate rectification:
The 12 crops and 21 track associations currently in the database for `TCIR_NIO_PILOT` reference Cyclone AMPHAN (2020) and Cyclone BIPARJOY (2023). However, published NTU CSIE TCIR only spans 2003–2017. The file `data/interim/tcir_nio_pilot.h5` was generated as a synthetic algorithmic fixture.

In Milestone F2.1 Phase B, this discrepancy is resolved via forward migration (Migration 006) adding explicit provenance tracking (`verification_status`) and isolating synthetic fixtures from authentic operational and ML training data.

