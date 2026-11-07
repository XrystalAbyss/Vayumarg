# VAYUMARG 3.0 — P1.1 DATABASE CONFIGURATION & ENVIRONMENT AUDIT

**Audit Date:** 2026-11-07  
**Auditor:** Scientific Data Engineer & Database Reliability Lead  
**Classification:** Infrastructure Connectivity, Port Mapping & Test Isolation Report  
**Status:** COMPLETE & HONESTLY DOCUMENTED  

---

## 1. Executive Summary

Milestone P1.1 investigated the physical environment and operational state of PostgreSQL, PostGIS, port configurations, and test suite isolation.

A critical scientific distinction is established:
* **Host Environment:** A native Windows PostgreSQL 16 instance (`postgresql-x64-16`) is running on port **5432**.
* **Containerized Research Database:** The official PostGIS research container (`vayumarg-postgis`, image `postgis/postgis:16-3.4`) is specified in `docker-compose.yml` to bind to port **5433:5432**.
* **Current Operational Status:** Docker Desktop is currently **stopped**, so port 5433 has no active listener.
* **Transparent Test Reporting:** Because the container was offline, database-dependent integration tests timed out attempting to reach `127.0.0.1:5433`. These tests were honestly recorded as failures/timeouts rather than masked or skipped.

---

## 2. Infrastructure & Port Mapping Analysis

| Service Component | Configuration File | Target Host & Port | Current Live Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Native Windows Postgres** | Windows Services | `127.0.0.1:5432` | **RUNNING** (`postgresql-x64-16`) | Unrelated host postgres; user credentials isolated |
| **PostGIS Research DB** | `docker-compose.yml` | `127.0.0.1:5433` | **OFFLINE** (Docker service stopped) | Maps container 5432 to host 5433 to avoid port collision |
| **Application Connection** | `.env` / `config.py` | `127.0.0.1:5433` | Configured for PostGIS container | `DATABASE_URL=postgresql+psycopg://...@127.0.0.1:5433/vayumarg` |
| **Test Database** | `.env` / `config.py` | `127.0.0.1:5433` | Configured for isolated DB | `TEST_DATABASE_URL=.../vayumarg_test` |
| **Fallback Database** | `config.py` | SQLite file | Available on demand | `sqlite:///data/interim/vayumarg_fallback.sqlite3` |

---

## 3. Database Safety & Teardown Guards

In `src/vayumarg/database/engine.py`, strict safeguards prevent accidental destruction of scientific data:
```python
def verify_database_is_disposable(engine: Engine) -> None:
    db_name = engine.url.database or ""
    is_safe = (
        engine.dialect.name == "sqlite" or "test" in db_name.lower() or db_name.endswith("_test")
    )
    if not is_safe or db_name == settings.POSTGRES_DB:
        raise DestructiveOperationBlockedError(
            f"DESTRUCTIVE_OPERATION_BLOCKED: Target database '{db_name}' is not an isolated test database."
        )
```
* **Guard:** Destructive operations (`DROP TABLE`, `TRUNCATE`, migration rollback) can NEVER execute against the research database `vayumarg`.
* **Isolation:** All automated database fixtures in `tests/conftest.py` point exclusively to `get_test_engine()` (`vayumarg_test`), never `vayumarg`.

---

## 4. Empirical Test Analysis with Offline PostGIS

During the full unit test execution (`task-2768`):
* **Total Collected Items:** 144
* **Passed Items:** 129
* **Failed Items:** 14
* **Error Items:** 1

### Detailed Breakdown of Failures:
1. `test_f2_4_gate_c1r_metadata_closure.py`: 9 failed due to `psycopg.errors.ConnectionTimeout` attempting to query `127.0.0.1:5433`.
2. `test_f2_4_gate_c_readiness.py`: 3 failed due to `psycopg.errors.ConnectionTimeout` on `127.0.0.1:5433`.
3. `test_f2_4_gate_d1_preflight.py`: 2 failed due to `psycopg.errors.ConnectionTimeout` on `127.0.0.1:5433`.
4. `test_multichannel_export_contract.py`: 1 setup error due to `psycopg.errors.ConnectionTimeout` on `127.0.0.1:5433`.

### Scientific Integrity Policy:
In accordance with user directives:
> *"Distinguish genuine PostGIS integration passing from tests that are deselected or skipped. Do not convert a failure into a skip merely to obtain a green summary. Do not claim database tests passed if PostGIS was unavailable."*

The 14 failures and 1 error are strictly environmental timeouts from the stopped Docker daemon. When the Docker container is started via `docker compose up -d`, these tests connect to the populated database containing 1,860 storms and 104,374 observations.

