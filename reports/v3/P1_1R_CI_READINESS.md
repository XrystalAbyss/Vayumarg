# VAYUMARG 3.0 — P1.1R CI READINESS REPORT

## 1. CI Pipeline Architecture

An unprivileged GitHub Actions workflow has been authored and committed at `.github/workflows/ci.yml`. It defines 4 isolated jobs designed to provide automated verification without requiring host-level administrative privileges.

```mermaid
flowchart TD
    A[Push / PR Event] --> B[Job 1: UNIT_NO_EXTERNAL_DB]
    A --> C[Job 2: POSTGIS_INTEGRATION]
    A --> D[Job 3: FRONTEND_BUILD]
    A --> E[Job 4: SCIENTIFIC_CONTRACT_CHECKS]
    
    B --> B1[25 Non-DB Test Files / 129 Tests]
    C --> C1[Docker Service postgis/postgis:16-3.4]
    C1 --> C2[15 DB & Gate C/D Tests]
    D --> D1[Node 20 / npm run build]
    E --> E1[OpenAPI Semantic Parity Diff]
    E --> E2[13 Scientific Numerical Invariants]
    E --> E3[Evidence JSON Metrics Validation]
```

---

## 2. Granular Job Specifications

### Job 1: `UNIT_NO_EXTERNAL_DB`
- **Environment**: Ubuntu Latest, Python 3.12.
- **Scope**: Runs 129 isolated unit tests across 25 test modules.
- **Database Dependency**: Zero. Uses `DATABASE_URL: sqlite:///:memory:` or pure mock fixtures.
- **Pass Guarantee**: 100% verified passing locally.

### Job 2: `POSTGIS_INTEGRATION`
- **Environment**: Ubuntu Latest, Python 3.12.
- **Service Container**: `postgis/postgis:16-3.4` mapped to `5433:5432`.
- **Health Check**: `pg_isready` polling with 10s interval, 5s timeout, 5 retries.
- **Database Target**: `postgresql+psycopg://vayumarg:vayumarg_secure_password@localhost:5433/vayumarg_test`.
- **Scope**: Runs `tests/integration/`, `test_f2_4_gate_c1r_metadata_closure.py`, `test_f2_4_gate_c_readiness.py`, `test_f2_4_gate_d1_preflight.py`, and `test_multichannel_export_contract.py`.

### Job 3: `FRONTEND_BUILD`
- **Environment**: Ubuntu Latest, Node.js 20.
- **Scope**: `npm ci` and `npm run build`.
- **Validation**: Strict TypeScript typechecking (`tsc -b`) and asset bundling.

### Job 4: `SCIENTIFIC_CONTRACT_CHECKS`
- **Environment**: Ubuntu Latest, Python 3.12.
- **Steps**:
  1. `python scripts/backup/openapi_semantic_diff.py`: Asserts 0 missing/changed endpoints across all 47 routes.
  2. `python scripts/backup/verify_scientific_numerical_parity.py`: Asserts exact numerical parity across all 13 items.
  3. Evidence validation: Validates `docs/evidence/hybrid_track_evaluation_summary.json` structure and key baselines.

---

## 3. Local vs CI Parity Ledger

| Verification Domain | Local Windows Environment | GitHub Actions CI Runner |
| :--- | :--- | :--- |
| **Python Unit Tests** | 129 / 129 Passed (100%) | Verified in `UNIT_NO_EXTERNAL_DB` |
| **PostGIS Database Tests** | Blocked by local Docker daemon service permissions | Automated via `postgis/postgis:16-3.4` container |
| **OpenAPI Contract** | 47 / 47 Routes Parity Verified | Automated via `SCIENTIFIC_CONTRACT_CHECKS` |
| **Numerical Parity** | 13 / 13 Items Verified (0 diff) | Automated via `SCIENTIFIC_CONTRACT_CHECKS` |
| **Frontend Build** | Built in 4.61s (0 errors) | Automated via `FRONTEND_BUILD` |
