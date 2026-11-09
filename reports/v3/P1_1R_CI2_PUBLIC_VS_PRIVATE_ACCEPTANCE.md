# Vayumarg 3.0 — P1.1R-CI.2 Public vs. Private Verification Boundary Specification

**Author:** Independent Research Software Verification Engineer  
**Date:** 2026-11-09  
**Milestone:** P1.1R-CI.2 (Verification Integrity & Gate Closure)  

---

## 1. Principles of Verification Integrity

Scientific software in weather and climate research frequently operates at the boundary between open-source mathematical engines and restricted, proprietary, or high-volume physical datasets.

Vayumarg 3.0 enforces a strict separation of concerns:
1. **Public Open-Source CI:** Must execute and pass in a clean, isolated runner with zero proprietary binaries, zero secret API tokens, and zero uncommitted binary datasets.
2. **Private Research Acceptance:** Validates models, neural weights, and large satellite arrays against experimental ground truth.
3. **Zero False Claims:** Untrained models must NEVER be presented as validated neural predictions. Tests that cannot execute due to missing private assets must report `SKIPPED (NOT_EXECUTED_PRIVATE_DATA)` and must NEVER masquerade as passed.

---

## 2. Four-Layer Parity Verification Architecture

The scientific numerical parity test harness (`scripts/backup/verify_scientific_numerical_parity.py`) has been restructured into four explicit, verifiable layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VAYUMARG VERIFICATION SUITE                  │
├─────────────────────────────────────────────────────────────────┤
│ Layer E1: Public Mathematical Tests (Kinematics & Invariants)   │
│   ├── Coordinate round-trip (lat/lon <-> dx/dy)                 │
│   ├── Closed-form Haversine distance parity (< 0.01 km)         │
│   └── Leakage Shield & Geodesic Extrapolation                   │
│   STATUS: PUBLIC_MATH_VERIFIED (Mandatory in Public CI)        │
├─────────────────────────────────────────────────────────────────┤
│ Layer E2: Architecture Contract Smoke Tests                     │
│   ├── Vision CNN: CycloneCNNRegressor shape contracts           │
│   ├── Vision ConvLSTM: CycloneConvLSTM spatiotemporal shapes    │
│   ├── Track GRU: VayumargTrackGRU recurrence contracts          │
│   └── Track Hybrid: VayumargHybridTrackModel residual heads     │
│   STATUS: ARCHITECTURE_SMOKE_TEST (Untrained Structural Smoke)  │
├─────────────────────────────────────────────────────────────────┤
│ Layer E3: Private Checkpoint Scientific Tests                   │
│   ├── TrackInferenceEngine multi-horizon predictions            │
│   ├── ResNet-18 IR authentic forward pass                       │
│   └── ConvLSTM authentic spatiotemporal forward pass            │
│   STATUS: PRIVATE_CHECKPOINT_VERIFIED or NOT_EXECUTED_PRIVATE   │
├─────────────────────────────────────────────────────────────────┤
│ Layer E4: Genuine INSAT Radiometric Validation                  │
│   ├── Physical crop brightness temperature quantiles            │
│   ├── ISRO calibration floor enforcement (min BT >= 179.80 K)   │
│   └── Dynamic PNG colormap rendering (> 10 kB)                  │
│   STATUS: GENUINE_INSAT_VERIFIED or NOT_EXECUTED_PRIVATE        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer Status Definitions

| Status Code | Environment | Execution Scope | Release Implication |
|---|---|---|---|
| **`PUBLIC_MATH_VERIFIED`** | Public CI & Local | Mathematical functions, coordinate transformations, haversine metrics, temporal leakage shields | **Mandatory:** Failure blocks CI and PR merge |
| **`ARCHITECTURE_SMOKE_TEST`** | Public CI & Local | Untrained PyTorch network instantiation, tensor dimension contracts, forward-pass gradient-free shape checks | **Mandatory:** Confirms code structure is sound without claiming trained accuracy |
| **`PRIVATE_CHECKPOINT_VERIFIED`** | Local / Research Stn | Loads authentic `.pt` binaries (`satellite_cnn_best.pt`, `track_gru_best.pt`, etc.) and asserts deterministic floats | Confirms model weights preserve verified meteorological predictions |
| **`GENUINE_INSAT_VERIFIED`** | Local / Research Stn | Opens authentic ISRO L1B HDF5 arrays, computes physical brightness temperatures, verifies radiometric colormaps | Confirms sensor calibrations match ISRO SAC specifications |
| **`NOT_EXECUTED_PRIVATE_DATA`** | Public CI | Emitted when `.pt` or `.h5` files or 1,860-storm DB rows are absent from the open repository | **Accepted in Public CI:** Transparently documents unexecuted tests without false passes |

---

## 4. Integrity Summary

By enforcing this four-layer architecture:
- Public GitHub Actions runs prove that all code, dependencies, schemas, and kinematics function reliably without external dependencies.
- Local research runs prove that trained weights and authentic INSAT imagery produce physically sound predictions.
- No false claims are made in public reports regarding model accuracy when only structural smoke tests have been executed.
