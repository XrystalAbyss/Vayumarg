# Vayumarg Milestone F0.1: Database Identity, Migration Safety and Scientific Integrity Hardening
**Acceptance & Engineering Verification Report**

**Milestone:** F0.1 — Hardening & IBTrACS Ingestion Readiness  
**Project:** Vayumarg (SIH 2026 / Problem Statement SIH26070 / Team VortexA)  
**Date:** November 1, 2026  
**Status:** **READY FOR REVIEW**  
**Review Lead:** Senior Database Architect, Scientific Data Engineer & QA Lead  

---

## 1. Executive Summary

Milestone F0.1 addresses specific foundation risks identified after the F0 bootstrap, ensuring scientific rigor, database safety, and robust identity governance prior to the ingestion of authentic NOAA IBTrACS data.

All objectives have been implemented, verified, and backed by empirical evidence:
- **Storm Identity Fixed:** The restrictive `UNIQUE(canonical_name, season_year, primary_basin)` constraint was removed via forward Alembic migration `002_storm_identity_and_safety`. Multiple unnamed storms and distinct storms sharing names now coexist seamlessly with immutable UUID primary keys.
- **Source Namespace & Revision Lineage:** Scoped uniqueness in `storm_aliases` protects source identities (e.g. IBTrACS SID). Observations now incorporate `is_superseded` and deterministic asset-scoped keys (`source_asset_id, source_record_id`), guaranteeing idempotency while preserving historical snapshots upon post-season revision.
- **Test Database Isolation:** Automated integration tests execute strictly against an isolated database (`vayumarg_test`). Destructive operations against the persistent research database (`vayumarg`) are blocked by active safety assertions (`DestructiveOperationBlockedError`).
- **Repeatable Backup/Restore:** Verified repeatable containerized backup and restore using PostgreSQL native `pg_dump` and `psql` tools on disposable fixtures.
- **WDAC Investigation:** Disproved the effectiveness of `DISABLE_SQLALCHEMY_CEXT` (unrecognized in SQLAlchemy 2.1+). Demonstrated that SQLAlchemy 2 Cython C-extensions run natively without environment tampering in clean processes, and documented the pure-Python fallback mechanism.
- **Test Results:** Expanded the automated suite from 20 to **31 passing tests (100% pass rate in 3.89s)**, comprising 17 real PostGIS integration tests and 14 unit tests.

---

## 2. Investigation of Initial F0 Baseline & Discrepancies

| Aspect | Initial Assumption / Claim | Actual Finding in Phase 1 & 5 | Resolution in F0.1 |
| :--- | :--- | :--- | :--- |
| **Storm Uniqueness** | `UNIQUE(canonical_name, season_year, primary_basin)` ensures clean storm entities. | **Defect Confirmed.** In climatological records, multiple tropical depressions in the same basin/season are labeled "UNNAMED" or "DEPRESSION". The constraint crashes on real multi-depression seasons. | Dropped `uq_storm_canonical` via forward migration `002`. Verified unnamed cyclones and same-name storms coexist. |
| **Observation Lineage** | `UNIQUE(storm_id, source_agency, observation_time_utc, source_record_id)` handles observation uniqueness. | **Risk Confirmed.** When NOAA re-releases revised best-track datasets (e.g., v04r00 to v04r01), reusing synoptic record IDs would either collide or require destructive overwrites. | Added `is_superseded` column and asset-scoped uniqueness `UNIQUE(source_asset_id, source_record_id)`. Older observations remain preserved as historical snapshots. |
| **WDAC Mitigation** | `DISABLE_SQLALCHEMY_CEXT=1` bypassed Windows Defender Application Control. | **Disproved.** Grepping SQLAlchemy 2.1.6 source code revealed `DISABLE_SQLALCHEMY_CEXT` is completely unreferenced. The original error was a transient Windows file lock while scanning the newly downloaded `.pyd`. | Tested fresh subprocesses without environment variables; confirmed `_util_cy.pyd` loads natively (`_is_compiled() == True`). Added regression test. |
| **Database Isolation** | Integration tests ran against `get_default_engine()`. | **Defect Confirmed.** Test fixtures were writing and rolling back directly in the primary research database (`vayumarg`). | Created isolated `vayumarg_test` database with PostGIS; reconfigured test suite and added safety assertion `verify_database_is_disposable()`. |

---

## 3. Detailed Verification Results (Phase 6 Matrix)

| Test / Requirement | Type | Status | Verified Evidence |
| :--- | :--- | :--- | :--- |
| **1. Two unnamed storms, same season/basin** | Integration | **PASSED** | Two `UNNAMED` depressions in BOB 2024 persisted with distinct UUIDs (`test_unnamed_storms_same_season_and_basin_coexist`). |
| **2. Two distinct storms sharing canonical name**| Integration | **PASSED** | Cyclones `GULAB` in BOB and ARB persisted as separate entities (`test_distinct_storms_sharing_canonical_name_coexist`). |
| **3. Duplicate source identifier rejection** | Integration | **PASSED** | Attempt to register identical IBTrACS SID `2024140N10085` to a second storm rejected with `IntegrityError` (`uq_agency_storm_alias`). |
| **4. Conflicting agency aliases** | Integration | **PASSED** | Multiple distinct agencies (IMD, JTWC, IBTrACS) successfully mapped distinct aliases to the same canonical storm. |
| **5. Multiple agency observations at same timestamp**| Integration | **PASSED** | IMD (3-min MSW) and JTWC (1-min MSW) observations for the same storm and hour coexisted without collision (`test_agency_convention_preservation_coexistence`). |
| **6. Deterministic observation identity** | Integration | **PASSED** | Scoped `(source_asset_id, source_record_id)` constraint strictly rejected duplicate record ingestion. |
| **7. Duplicate import idempotency** | Integration | **PASSED** | Re-importing exact same asset record raised IntegrityError, preventing row duplication. |
| **8. Source revision handling** | Integration | **PASSED** | Ingesting revised asset v2 preserved asset v1 observation (`is_superseded=True`) alongside revised observation (`is_superseded=False`). |
| **9. Test database isolation** | Integration | **PASSED** | Verified tests bind strictly to `vayumarg_test`. Audited `vayumarg` table counts remained exactly 0 across all 8 tables. |
| **10. Destructive operation blocked on non-test DB**| Integration | **PASSED** | Calling `verify_database_is_disposable()` against `vayumarg` raised `DestructiveOperationBlockedError`. |
| **11. Backup and restore cycle** | Integration | **PASSED** | End-to-end `pg_dump` and `psql` restore cycle on disposable records executed with verified post-restore integrity. |
| **12. Fresh-process WDAC compatibility** | Unit | **PASSED** | Subprocess executed with stripped environment imported SQLAlchemy 2.1.6 cleanly (`_is_compiled() == True`). |
| **13. Existing F0 regression suite** | Unit / Int | **PASSED** | All 20 original F0 tests passed without regressions alongside the 11 new tests (31/31 passed). |

---

## 4. Test Execution Log

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\astra\Desktop\Project\Vayumarg\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\astra\Desktop\Project\Vayumarg
configfile: pyproject.toml
testpaths: tests
plugins: asyncio-1.4.1, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 31 items

tests/integration/test_database_integrity.py::test_postgis_extension_available PASSED [  3%]
tests/integration/test_database_integrity.py::test_synthetic_data_insertion_and_foreign_keys PASSED [  6%]
tests/integration/test_database_integrity.py::test_duplicate_source_rejection PASSED [  9%]
tests/integration/test_database_integrity.py::test_invalid_latitude_rejection PASSED [ 12%]
tests/integration/test_database_integrity.py::test_invalid_longitude_rejection PASSED [ 16%]
tests/integration/test_database_integrity.py::test_null_missing_data_preservation PASSED [ 19%]
tests/integration/test_database_integrity.py::test_agency_convention_preservation_coexistence PASSED [ 22%]
tests/integration/test_database_integrity.py::test_transaction_rollback_guarantee PASSED [ 25%]
tests/integration/test_database_safety.py::test_test_database_isolation PASSED [ 29%]
tests/integration/test_database_safety.py::test_destructive_operation_blocked_on_production_database PASSED [ 32%]
tests/integration/test_database_safety.py::test_backup_and_restore_cycle PASSED [ 35%]
tests/integration/test_storm_identity_and_revisions.py::test_unnamed_storms_same_season_and_basin_coexist PASSED [ 38%]
tests/integration/test_storm_identity_and_revisions.py::test_distinct_storms_sharing_canonical_name_coexist PASSED [ 41%]
tests/integration/test_storm_identity_and_revisions.py::test_duplicate_source_identifier_within_agency_rejected PASSED [ 45%]
tests/integration/test_storm_identity_and_revisions.py::test_distinct_agencies_can_alias_same_storm PASSED [ 48%]
tests/integration/test_storm_identity_and_revisions.py::test_deterministic_observation_identity_and_duplicate_rejection PASSED [ 51%]
tests/integration/test_storm_identity_and_revisions.py::test_source_revision_preserves_old_observations_and_links_new_asset PASSED [ 54%]
tests/unit/test_config.py::test_default_settings PASSED                  [ 58%]
tests/unit/test_config.py::test_data_dir_resolution PASSED               [ 61%]
tests/unit/test_contracts.py::test_valid_data_source_contract PASSED     [ 64%]
tests/unit/test_contracts.py::test_source_asset_invalid_sha256 PASSED    [ 67%]
tests/unit/test_track_observation_contract_coordinate_validation PASSED [ 70%]
tests/unit/test_contracts.py::test_track_observation_utc_coercion PASSED [ 74%]
tests/unit/test_hashing.py::test_bytes_sha256 PASSED                     [ 77%]
tests/unit/test_hashing.py::test_file_sha256 PASSED                      [ 80%]
tests/unit/test_hashing.py::test_generate_and_save_manifest PASSED       [ 83%]
tests/unit/test_quality_validation.py::test_coordinate_validator PASSED  [ 87%]
tests/unit/test_quality_validation.py::test_agency_averaging_convention_validation PASSED [ 90%]
tests/unit/test_quality_validation.py::test_suspicious_zero_wind_speed_detection PASSED [ 93%]
tests/unit/test_wdac_compatibility.py::test_fresh_process_import_without_workaround PASSED [ 96%]
tests/unit/test_wdac_compatibility.py::test_sqlalchemy_util_cy_distill_params PASSED [100%]

============================= 31 passed in 3.89s ==============================
```

---

## 5. Security & Configuration Audit

- **Environment Credentials:** Development passwords (`vayumarg_dev_password`) are restricted to local development templates; `.env` remains ignored by git.
- **Network Isolation:** PostGIS container exposes port 5433 only on localhost (`127.0.0.1:5433`); no public exposure.
- **Log Credential Sanitization:** Verified that passwords and secrets are redacted by `SanitizingFormatter`.
- **Destructive Operation Blocker:** Hardcoded barrier `verify_database_is_disposable()` prevents automated test suites or migration downgrade scripts from clearing the production/research database.

---

## 6. Readiness for Milestone F1 (NOAA IBTrACS Ingestion)

With Milestone F0.1 completed:
1. IBTrACS SIDs (e.g. `2020136N10087`) will map directly and cleanly to `storm_aliases.agency_storm_id`.
2. Unnamed historical tropical depressions in the North Indian Ocean will not violate unique constraints.
3. Multiple agencies compiled inside IBTrACS (IMD, JTWC, BOM, CMA) can be ingested into `track_observations` at the same synoptic timestamp without collision.
4. Any post-season revisions from NOAA NCEI will be ingested as new assets without destroying previous historical snapshots.

**Verdict:** **READY TO BEGIN MILESTONE F1 INGESTION.**

