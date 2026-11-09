# Vayumarg 3.0 — P1.1R-CI.2 Scientific Baseline Parity Report

**Author:** Independent Research Software Verification Engineer  
**Date:** 2026-11-09  
**Milestone:** P1.1R-CI.2 (Verification Integrity & Gate Closure)  
**Protected Baseline Tag:** `v3.0.0-pre-refactor-baseline` (`288fd2cd61b9ec81cdef6ee939559d7a53adc480`)  
**Development Head:** `feat/v3-p1-backend-stabilization`  

---

## 1. Baseline Preservation Audit

The protected baseline tag `v3.0.0-pre-refactor-baseline` freezes the historical research software prior to modularization. A byte-level git audit confirms:
- **Baseline Commit:** `288fd2cd61b9ec81cdef6ee939559d7a53adc480` (Untouched, verified).
- **Public Main:** `d467a1c0cd22a07c4cdd5376ca8c9bd9851d22b4` (Untouched, verified).
- **Refactoring Strategy:** Zero architectural changes were committed directly to `main`. All work was isolated on branch `feat/v3-p1-backend-stabilization`.

---

## 2. OpenAPI Semantic Parity Verification

The refactored backend transitioned from a monolithic 1,151-line `server.py` into modular routers in `src/vayumarg/api/routers/` and domain services in `src/vayumarg/services/`.

A deterministic OpenAPI diff was executed between the baseline specification (`reports/v3/baseline_openapi.json`) and the current application (`app.openapi()`):

```
============================================================
OPENAPI SEMANTIC COMPARISON RESULTS
============================================================
Baseline paths count: 47
Current paths count:  47
Missing paths:        []
Added paths:          []

Total Endpoint Parameter / Method / Status Discrepancies: 0

Baseline Schemas: 24
Current Schemas:  24
Missing Schemas:  []
Added Schemas:    []
============================================================
SEMANTIC PARITY CONFIRMED: 100% MATCH ACROSS ALL 47 ENDPOINTS
```

Every HTTP route, query parameter, request body, and response schema has been preserved with zero breaking changes.

---

## 3. Mathematical & Kinematic Parity

The deterministic verification suite executed 4 mathematical invariants comparing baseline and refactored code:

### 3.1 Closed-Form Haversine Parity
- **Baseline (`calculate_haversine_distance_km`):** 56.59 km (formatted with 2 decimal precision).
- **ML Engine (`haversine_km`):** 56.591468 km (full precision float).
- **Difference:** $0.001468\text{ km} < 0.01\text{ km}$ tolerance limit. The minute difference is purely due to display rounding in Module B.

### 3.2 Coordinate System Round-Trip Inversion
- Spherical coordinates $(18.25^\circ\text{N}, 67.85^\circ\text{E})$ converted to Cartesian $(dx, dy)$ relative to $(18.0^\circ\text{N}, 67.5^\circ\text{E})$, then inverted back to spherical coordinates.
- **Latitude Inversion Error:** $0.00000000^\circ$ ($< 10^{-5\circ}$).
- **Longitude Inversion Error:** $0.00000000^\circ$ ($< 10^{-5\circ}$).

### 3.3 Leakage Shield Invariant
- **Fixture:** Cyclone BIPARJOY track history.
- **Cutoff Timestamp:** `2023-06-11T06:00:00Z`.
- **Pre-issue Observations:** Exactly 51 observations isolated.
- **Post-issue Observations in Forecast Input:** Exactly 0 (Zero future leakage).
- **Extrapolated +6h Point:** Lat $18.60^\circ\text{N}$ (strictly progresses northward along verified track).

---

## 4. PyTorch Model Checkpoint Checksums

All four original trained checkpoints were independently verified against the authoritative cloud registry (`reports/v3/checkpoint_cloud_registry.json`). Zero bytes were modified:

| Checkpoint Identifier | File Location | Physical Size | Verified SHA-256 Checksum | Match Status |
|---|---|---|---|---|
| **ResNet-18 IR CNN** | `models/vayumarg/vision/satellite_cnn_best.pt` | 44,792,059 B | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | EXACT MATCH |
| **Spatiotemporal ConvLSTM** | `models/vayumarg/vision/satellite_convlstm_best.pt` | 15,224,965 B | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | EXACT MATCH |
| **Recurrent Track GRU** | `models/vayumarg/track_gru_best.pt` | 1,489,521 B | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | EXACT MATCH |
| **Track Hybrid Residual** | `models/vayumarg/track_hybrid_residual_best.pt` | 382,239 B | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` | EXACT MATCH |

Zero quantization, zero weight pruning, zero architecture re-definitions occurred. Full scientific parity is sustained.
