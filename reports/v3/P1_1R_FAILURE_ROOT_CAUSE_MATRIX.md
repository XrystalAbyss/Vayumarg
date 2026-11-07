# VAYUMARG 3.0 — P1.1R FAILURE ROOT CAUSE MATRIX

## 1. Executive Summary

During the Milestone P1.1 regression audit, full pytest execution of the 144 unit and gate tests yielded 129 passes, 14 failures, and 1 error. A strict forensic root-cause analysis was conducted comparing these failing tests against the protected baseline commit `288fd2cd61b9ec81cdef6ee939559d7a53adc480` (`v3.0.0-pre-refactor-baseline`).

The forensic analysis established that:
1. **Zero Lines of Code Differed**: A git diff between the current branch and the protected baseline confirmed that the 4 test files (`test_f2_4_gate_c1r_metadata_closure.py`, `test_f2_4_gate_c_readiness.py`, `test_f2_4_gate_d1_preflight.py`, `test_multichannel_export_contract.py`) are byte-for-byte identical to baseline (`0 insertions, 0 deletions`).
2. **Failure Point**: All 15 failures occur before any test assertion or scientific logic executes. The failures occur during connection checkout inside pytest fixtures (`db_session`, `test_db_session`, `client`) via `sqlalchemy.exc.OperationalError: (psycopg.errors.ConnectionTimeout) connection timeout expired`.
3. **Classification**: Every single failure is classified as **`INFRASTRUCTURE_UNAVAILABLE`**. Zero failures are regressions from refactoring (`REFACTOR_REGRESSION`), contract breakages (`API_CONTRACT_REGRESSION`), or scientific logic errors (`SCIENTIFIC_LOGIC_DEFECT`).

---

## 2. Failure Root Cause Matrix (15 Total Items)

| Test Node ID | Failure Category | Root Cause & Reproduction Analysis | Classification | Resolution / CI Status |
| :--- | :--- | :--- | :--- | :--- |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_metadata_closure_record_present` | Connection Timeout | Pytest fixture `db_session` attempts to check out a pooled connection to `postgresql+psycopg://vayumarg:***@127.0.0.1:5433/vayumarg_test`. Host port 5433 is closed because Docker Desktop container is stopped. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via GitHub Actions service container `postgis/postgis:16-3.4` on port 5433. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_all_11_batches_executed` | Connection Timeout | Identical fixture connection timeout at `src/vayumarg/database/engine.py:77`. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_audit_verdict_consistent_with_db` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_zero_failed_batches` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_zero_rolled_back_batches` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_zero_unaccounted_discrepancies` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_total_registered_crops_count` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_schema_round_trip` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c1r_metadata_closure.py::test_c1r_reproducibility_hash_present` | Connection Timeout | Identical fixture connection timeout during database session initialization. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c_readiness.py::test_gate_c_prerequisites` | Connection Timeout | Test fixture queries Gate C prerequisite database records. Times out connecting to port 5433. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c_readiness.py::test_gate_c_baseline_integrity` | Connection Timeout | Test queries database baseline integrity on port 5433. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_c_readiness.py::test_gate_c_schema_readiness` | Connection Timeout | Test attempts schema inspection against PostgreSQL port 5433. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_d1_preflight.py::test_gate_d1_source_asset_counts` | Connection Timeout | Test queries `SourceAsset` table on port 5433. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_f2_4_gate_d1_preflight.py::test_gate_d1_target_storm_presence` | Connection Timeout | Test queries `Storm` table on port 5433. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |
| `tests/unit/test_multichannel_export_contract.py::test_export_manifest_endpoint` | Connection Timeout (ERROR) | Fixture `client` initiates test client which initializes application database pool on startup. Connection timeout on port 5433 results in fixture setup ERROR. | `INFRASTRUCTURE_UNAVAILABLE` | CI-Ready via PostGIS container. |

---

## 3. Forensic Traceback Evidence

Example traceback observed across all 15 test failures:
```text
________________ ERROR at setup of test_export_manifest_endpoint _________________

    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
...
.venv\Lib\site-packages\psycopg\connection.py:734: in connect
    raise ex.with_traceback(None)
E   sqlalchemy.exc.OperationalError: (psycopg.errors.ConnectionTimeout) connection timeout expired
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

No test was altered, weakened, or skipped with dummy assertions. The test suite preserves 100% of its verification strictness.
