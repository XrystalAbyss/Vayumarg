# VAYUMARG 3.0 — P0 ARCHITECTURE DECISION RECORD (ADR)

**Status:** APPROVED FOR VAYUMARG 3.0 DESIGN  
**Date:** 7 November 2026  
**Auditor:** Full-Stack Software Architect, Systems Engineer & Scientific Lead  
**Scope:** Core System Architecture, Data Contracts & API Governance  

---

## ADR-001: Preservation of Historical Baseline (`v2.2.3-freeze`)

### Context
Vayumarg reached an operational milestone during the hackathon (tagged internally as `v2.2.3-freeze`). However, the repository currently resides in an untracked zero-commit state. Without an immediate commit, refactoring risks erasing the working hackathon prototype.

### Decision
Immediately create a foundational Git commit containing all existing source code, tests, manifests, and documentation, and attach an annotated tag `v2.2.3-freeze`. Subsequent Vayumarg 3.0 development will proceed on feature branches branched from this tagged state.

### Consequences
- Guarantees complete rollback safety to a functioning baseline.
- Preserves the historical evidence base for external auditors and judges.

---

## ADR-002: Modular Decoupling of Monolithic `server.py`

### Context
`src/vayumarg/api/server.py` currently spans 1,151 lines, combining FastAPI routing, raw database SQL queries, file system I/O, mathematical transformations, and response serialization in a single file.

### Decision
Refactor `server.py` into a clean modular structure under `src/vayumarg/`:
1. `api/routers/`: Lightweight HTTP routers (`storms.py`, `forecast.py`, `satellite.py`, `ml.py`, `dataset.py`).
2. `services/`: Pure business and scientific logic (`forecast_service.py`, `satellite_service.py`, `storm_service.py`).
3. `contracts/`: Pydantic v2 data transfer schemas with strict field-level documentation.
4. `database/repositories/`: Encapsulated database query repositories isolating SQLAlchemy sessions from HTTP handlers.

### Consequences
- Eliminates monolithic code bloat.
- Allows independent unit testing of meteorological algorithms without mocking FastAPI HTTP request cycles.

---

## ADR-003: Strict Enforcement of Ground-Truth Leakage Protection & Issue-Time Gates

### Context
In operational meteorological forecasting, a forecast issued at time $t_{\text{issue}}$ can only utilize observations recorded at $t \le t_{\text{issue}}$. In retrospective evaluations, information leakage (such as normalizing over the entire storm lifecycle or using future fixes) leads to artificially inflated accuracy claims.

### Decision
1. All database queries and memory lookups must enforce:
   $$\text{WHERE observation\_time\_utc} \le t_{\text{issue}}$$
2. Forecasting APIs must explicitly require an `issue_time_utc` parameter.
3. Automated regression tests must deliberately attempt future-data injection and assert that outputs remain bitwise identical.

### Consequences
- Prevents data leakage in operational simulation.
- Rejects unscientific look-ahead bias across all evaluation metrics.

---

## ADR-004: Dual-Engine Trajectory Strategy: Deterministic Baseline vs Experimental Neural

### Context
Forensic testing demonstrated that the deterministic constant-velocity geodesic baseline outperforms the recurrent Track GRU across all forecast horizons (+6h, +12h, +24h). The hybrid residual model showed promising reductions on the test partition, but this was derived after inspecting that specific test cohort.

### Decision
1. The **Deterministic Geodesic Baseline** is designated as the **Primary Production Operational Engine**.
2. The **Track GRU** and **Hybrid Residual Model** are categorized strictly as **`IMPLEMENTED_EXPERIMENTAL`**.
3. The API and user interface must present the deterministic geodesic trajectory as the default reference, displaying neural predictions as comparative experimental overlays with explicit skill scores.

### Consequences
- Prevents deploying a neural model that degrades accuracy relative to established physics.
- Maintains scientific transparency while continuing research into hybrid techniques.

---

## ADR-005: Separation of Observation, Estimation, and Prediction Conventions

### Context
Different agencies and models employ distinct physical wind averaging periods:
- IMD: 3-minute sustained wind in knots (RSMC New Delhi operational standard).
- JTWC: 1-minute sustained wind in knots (US Navy standard).
- WMO: 10-minute sustained wind consensus.
- ResNet-18 CNN: Predicts 1-minute sustained wind speed.

Conflating these standards or applying universal scalar multipliers ($0.88$) corrupts meteorological truth.

### Decision
1. All API contracts and database fields must explicitly state the observation convention and averaging period in the field name or metadata (e.g., `imd_wind_kt_3min`, `jtwc_wind_kt_1min`, `predicted_wind_kt_1min`).
2. No universal scalar multiplier shall be applied to coerce 1-minute predictions to 3-minute IMD targets.
3. The user interface must present observations and predictions in separate, labeled cards with an **Averaging Period Integrity** notice.

### Consequences
- Enforces meteorological standards compliance.
- Eliminates false comparisons between non-equivalent physical metrics.

---

## ADR-006: Radiometric Integrity & LUT Clamping Invariant

### Context
ISRO INSAT-3DR/3DS Level-1B imagery contains raw sensor counts converted to Brightness Temperature ($T_B$) in Kelvin using instrument-specific look-up tables (LUTs). The INSAT radiometric calibration enforces a hard floor at $179.86\text{ K}$, truncating ultra-cold convective tops.

### Decision
1. All satellite image processing pipelines must operate directly on physical Kelvin arrays ($180\text{ K} \le T_B \le 310\text{ K}$) rather than non-linear display stretchings.
2. The image processing engine must compute and preserve a boolean clamping mask (`arr <= 179.86`), surfacing clamping ratios in analytical endpoints (`clamped_low_temperature_pixels`).
3. Coregistered crops must be exported in standardized scientific containers (HDF5 or NetCDF4) with embedded metadata.

### Consequences
- Preserves raw physical measurements for scientific verification.
- Explicitly flags sensor instrument limitations to meteorologists.

---

## ADR-007: Standardized Host Database Port 5433 with Transparent Offline Fallback

### Context
Host port conflicts between native Windows PostgreSQL (5432) and Docker PostGIS caused intermittent connection failures during development and testing.

### Decision
1. Standardize host port mapping to **5433** (`"${POSTGRES_PORT:-5433}:5432"`).
2. Configure `.env.example` and `src/vayumarg/core/config.py` with port 5433 as canonical.
3. Maintain the automated offline fallback engine: if PostgreSQL on 5433 is unreachable, the system automatically falls back to `data/demo_cache/` to ensure zero-downtime demonstration.

### Consequences
- Eliminates port collision on developer machines.
- Provides seamless offline resilience.

---

## ADR-008: Sequestered Three-Tier Partitioning for Future ML Development

### Context
Developing models by iteratively evaluating on a single test set introduces model-selection bias and invalidates reported statistical confidence.

### Decision
For Vayumarg 3.0, all datasets must be partitioned into three strictly storm-disjoint tiers:
1. **Tier 1 (Training):** Used exclusively for gradient optimization and feature learning.
2. **Tier 2 (Validation / Development):** Used for hyperparameter tuning, checkpoint selection, and architectural exploration.
3. **Tier 3 (Confirmatory Test):** Cryptographically sequestered and evaluated **exactly once** upon final model release.

### Consequences
- Eliminates data leakage and evaluation bias.
- Restores rigorous scientific reproducibility.

