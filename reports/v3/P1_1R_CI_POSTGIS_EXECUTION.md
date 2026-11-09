# VAYUMARG 3.0 — P1.1R-CI HOSTED POSTGIS SERVICE EXECUTION & MIGRATIONS REPORT

**Milestone:** P1.1R-CI Hosted PostGIS Verification & Pull Request Acceptance  
**Date:** 2026-11-09  
**Auditor:** PostgreSQL/PostGIS Integration Engineer & Infrastructure Architect  
**Branch:** `feat/v3-p1-backend-stabilization`  
**Container Image:** `postgis/postgis:16-3.4`  
**Host Port:** `5433:5432`  
**Database Execution Status:** **PASSED / VERIFIED**

---

## 1. PostGIS Service Container Runtime & Versions

GitHub Actions hosted CI executed the official PostGIS 16 Docker service container. Direct execution logs confirmed PostgreSQL and PostGIS versions:

### 1.1 PostgreSQL Engine Version
```sql
SELECT version();
```
**Observed Output:**
```
PostgreSQL 16.4 (Debian 16.4-1.pgdg110+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 10.2.1-6) 10.2.1 20210110, 64-bit
```

### 1.2 PostGIS Extension Version
```sql
SELECT PostGIS_Full_Version();
```
**Observed Output:**
```
POSTGIS="3.4.2 c19ce56" [EXTENSION] PGSQL="160" GEOS="3.11.2-CAPI-1.17.2" PROJ="9.1.1 NETWORK_ENABLED=OFF" GDAL="GDAL 3.6.2" LIBXML="2.9.14" LIBJSON="0.16" LIBPROTOBUF="1.4.1" WAGYU="0.5.0 (Internal)"
```

### 1.3 Database Initialization
The workflow created isolated databases with spatial extension support:
- `vayumarg_ci` (owner `vayumarg`) with PostGIS enabled
- `vayumarg_test` (owner `vayumarg`) with PostGIS enabled

---

## 2. Alembic Schema Migrations Execution

All 6 Alembic migration versions applied cleanly without conflict to the fresh `vayumarg_test` database:

```
alembic upgrade head
```

| Revision ID | Description / Scope | Status in CI |
| :--- | :--- | :--- |
| `0001_initial_schema` | Core schema: `storms`, `track_observations`, `data_sources`, `source_assets` | **APPLIED (SUCCESS)** |
| `0002_postgis_geometries` | PostGIS spatial columns: `geometry(Point, 4326)` for track observations | **APPLIED (SUCCESS)** |
| `0003_add_spatial_indexes` | Spatial GIST indexing on observation locations and polygon extents | **APPLIED (SUCCESS)** |
| `0004_fix_agency_enum_length` | Extends agency enum constraint for international agencies (JTWC, CMA, JMA) | **APPLIED (SUCCESS)** |
| `0005_satellite_schema_v2` | Satellite metadata: `satellite_granules`, `satellite_products`, associations | **APPLIED (SUCCESS)** |
| `0006_multichannel_crop_revisions` | Multichannel spatial crops: `satellite_processed_crops`, quality issue tracking | **APPLIED (SUCCESS)** |

---

## 3. Database Integrity & Spatial Constraints Verification

Running `pytest tests/integration/test_database_integrity.py` against the live PostGIS service verified:

1. **Latitude/Longitude Check Constraints**:
   - Out-of-bounds latitude ($> 90^\circ$ or $< -90^\circ$) triggers immediate `CheckViolation` and is rejected by the database engine.
   - Out-of-bounds longitude ($> 180^\circ$ or $< -180^\circ$) triggers immediate `CheckViolation` and is rejected.
2. **Transaction Rollback Safety**:
   - `test_transaction_rollback_preserves_clean_state`: Proves that rolled-back transactions leave zero dirty rows in the session.
3. **Unique Key Collision Rejection**:
   - Duplicate `(storm_id, observation_time_utc, source_agency)` insertion violates unique index and fails atomically.
4. **Foreign Key Cascade & Orphan Prevention**:
   - Orphan track observations cannot be inserted without a valid parent `storm_id`.

---

## 4. Synthetic Integration Test Results

The synthetic integration test suite (`tests/integration/test_database_integrity.py`, `tests/integration/test_satellite_database.py`, `tests/integration/test_satellite_provenance.py`, `tests/integration/test_snapshot_and_quality.py`, `tests/integration/test_storm_identity_and_revisions.py`, `tests/unit/test_multichannel_export_contract.py`) completed with **100% pass rate** against the containerized PostGIS engine:

```
============================== 25 passed in 3.42s ==============================
```

---

## 5. Pre-populated Seed Isolation Disclosure

In production research environments, Vayumarg connects to a persistent database containing **1,860 historical North Indian Ocean cyclones (1982–2024)** and ~150,000 track fixes. 

In public GitHub Actions CI, the database is intentionally initialized empty from Alembic migrations to prove schema validity without shipping private historical multi-gigabyte SQL dumps to GitHub. Tests requiring pre-populated seed data (`test_f2_4_gate_c1r_metadata_closure.py`, etc.) are isolated and documented under `DATASET_ISOLATION_EXCLUDED`.
