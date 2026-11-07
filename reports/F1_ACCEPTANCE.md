# VAYUMARG — Milestone F1 Acceptance Verification Report

## 1. Milestone Objectives and Verification Summary

Milestone **F1: Authoritative North Indian Ocean Cyclone Database Ingestion** establishes the verified scientific baseline for Vayumarg.

| Phase | Core Objective | Acceptance Criteria | Status | Evidence / Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Phase A** | Baseline Preservation | F0/F0.1 baseline intact, PostGIS healthy on port 5433, 0 regression | **VERIFIED** | 31/31 baseline tests passed before changes. Zero data loss. |
| **Phase B** | Official Source Acquisition | Streamed atomic download with SHA-256 and size verification | **VERIFIED** | `ibtracs_ni_v04r01.csv` (27,895,917 bytes, SHA-256 `6e0dd...`). Manifest saved. |
| **Phase C & D** | Multi-Agency Row Identity | Support multi-agency observations per CSV row without collision | **VERIFIED** | Migration `003` applied. `UNIQUE(source_asset_id, source_record_id, source_agency)`. |
| **Phase E & F** | Parsing & Ingestion Engine | Deterministic parser, 2-row header handling, strict null preservation | **VERIFIED** | `IBTrACSParser` and `ibtracs_ingest.py` tested and verified. |
| **Phase G** | Pilot & Full Ingestion | Bounded pilot (AMPHAN, BIPARJOY) then full NI ingestion into `vayumarg` | **VERIFIED** | 1,860 storms and 104,374 observations ingested. Audit logged in `ingestion_runs`. |
| **Phase H** | Scientific Quality Audit | Authentic queries exported to Markdown and JSON | **VERIFIED** | `reports/F1_DATA_QUALITY.md` and `.json` generated. |
| **Phase I** | Module A & B Contracts | Typed export contracts distinguishing retrospective from operational | **VERIFIED** | `ModuleAExportRecord` & `ModuleBExportRecord` in `src/vayumarg/contracts/export.py`. |
| **Phase J** | CLI Capabilities | Working CLI commands for download, pilot, full, query, and audit | **VERIFIED** | All 10 CLI commands functional and verified with Rich formatting. |
| **Phase K** | Automated Testing | Comprehensive unit and integration test suite | **VERIFIED** | **37 / 37 tests passing** in 10.88s. Ruff clean (0 errors, 34 files formatted). |
| **Phase L** | Technical Documentation | Complete data and architecture guides produced | **VERIFIED** | 5 comprehensive technical documents delivered in `docs/data/`. |

---

## 2. Ingested Canonical Entity Verification

Verified against the canonical persistent research database `vayumarg`:

```
+---------------------+--------------+
| Table Name          | Record Count |
+---------------------+--------------+
| data_sources        | 1            |
| source_assets       | 1            |
| ingestion_runs      | 2            |
| storms              | 1,860        |
| storm_aliases       | 2,534        |
| track_observations  | 104,374      |
| data_quality_issues | 0            |
| dataset_snapshots   | 0            |
+---------------------+--------------+
```

### Ingestion Run Lineage
1. **Pilot Run (`c0fbbd29-57d9-4e14-af84-d2491dd7e3b2`):**
   - Target: Benchmark cyclones AMPHAN (2020) and BIPARJOY (2023).
   - Records Read: 164 raw rows.
   - Records Inserted: 462 observations.
   - Status: `COMPLETED`, Outcome: `COMMITTED`.
2. **Full Ingestion Run (`20011dd2-2900-47ab-bdb2-ab7e5e801332`):**
   - Target: Complete North Indian Ocean archive (1842 – 2026).
   - Records Read: 62,885 raw rows.
   - Records Inserted: 103,912 observations.
   - Records Skipped (Idempotent): 462 observations (AMPHAN/BIPARJOY already present).
   - Status: `COMPLETED`, Outcome: `COMMITTED`.

---

## 3. Scientific Verification Checklist

- [x] **Strict NULL Preservation:** Zero wind speed count is 0; zero pressure count is 0. Missing values are preserved as SQL NULL.
- [x] **Wind Averaging Period Segregation:** 3-minute sustained winds (IMD: 10,759 obs), 1-minute sustained winds (JTWC: 30,730 obs), and 10-minute sustained winds (WMO/IBTrACS: 62,885 obs) strictly segregated without artificial conversions.
- [x] **PostGIS Geometry:** All 104,374 observations have PostGIS SRID 4326 Point geometries correctly indexed with spatial R-tree indexing.
- [x] **Authoritative SIDs:** All 1,860 storms are indexed by authoritative NOAA IBTrACS SIDs in `storm_aliases` with confidence `1.0`.
- [x] **Idempotency Guarantee:** Re-executing pilot or full ingestion skips existing records without duplicate errors or constraint violations.
- [x] **Test Isolation:** Integration tests strictly target disposable `vayumarg_test` database. Persistent `vayumarg` database protected from destructive teardowns.

---

## 4. Verification Commands

```powershell
# 1. Run full test suite (37 tests)
.\.venv\Scripts\pytest.exe -v

# 2. Check code quality and style
.\.venv\Scripts\ruff.exe check src tests scripts
.\.venv\Scripts\ruff.exe format --check src tests scripts

# 3. Inspect canonical record counts
.\.venv\Scripts\python.exe -m vayumarg.api.cli counts

# 4. Query benchmark cyclone Amphan
.\.venv\Scripts\python.exe -m vayumarg.api.cli query-storm AMPHAN

# 5. Query benchmark cyclone Biparjoy
.\.venv\Scripts\python.exe -m vayumarg.api.cli query-storm BIPARJOY

# 6. Query historical 1842 cyclone
.\.venv\Scripts\python.exe -m vayumarg.api.cli query-storm 1842298N11080

# 7. Re-generate scientific quality audit
.\.venv\Scripts\python.exe -m vayumarg.api.cli audit-quality
```

