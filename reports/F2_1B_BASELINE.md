# F2.1B Baseline Verification Audit

**Milestone:** F2.1B  
**Date:** 2026-11-01  
**Project:** Vayumarg — Scientific Data Foundation (Team VortexA / SIH 2026 / CV-IP)  
**Auditor:** Principal Satellite Data Engineer & QA Lead  
**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  

---

## 1. System Environment & Pre-condition Checklist

- **Operating System:** Windows 11 Home Single Language (Build 26100), PowerShell shell.
- **Python Environment:** Python 3.12.10 (`.venv\Scripts\python.exe`) via `uv`.
- **Database Backend:** PostgreSQL 16.4 / PostGIS 3.4.3 running in Docker on `localhost:5433`.
- **Alembic Revision:** `006_satellite_provenance` (head verified).
- **Test Suite Status:** **58 passed in 12.60s** (0 failures, 0 errors).
- **Code Linter / Formatter:** Ruff 0.17.3 clean across `src`, `tests`, `scripts`, `migrations`.
- **Free Disk Capacity:** 179.15 GB on drive `C:`.

---

## 2. Table-by-Table Data Integrity & Snapshot Freeze Verification

| Table Name | Verified Count | Notes |
|:---|:---|:---|
| `data_sources` | 1 | Official NOAA NCEI IBTrACS |
| `source_assets` | 1 | `ibtracs.NI.list.v04r01.csv` |
| `ingestion_runs` | 2 | F1 Initial + F1.1 Reconciliation |
| `storms` | 1,860 | Intact canonical North Indian Ocean cyclones |
| `storm_aliases` | 2,534 | Cross-agency aliases |
| `track_observations` | 104,374 | Intact validated track observations |
| `data_quality_issues` | 8 | Persisted audit findings |
| `dataset_snapshots` | 1 | Freeze `vayumarg-nio-ibtracs-f1.1-freeze` |
| `satellite_products` | 10 | 9 official ISRO INSAT products + 1 TCIR pilot |
| `satellite_granules` | 1 | `TCIR_NIO_PILOT_2020_2023` (`SYNTHETIC_FIXTURE`) |
| `satellite_processed_crops` | 12 | 100% categorized as `SYNTHETIC_FIXTURE` |
| `satellite_track_associations` | 21 | 100% categorized as `SYNTHETIC_FIXTURE` |

- **Frozen Dataset Snapshot Hash:**
  `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`
  - 104,374 samples strictly preserved; zero mutation detected.

