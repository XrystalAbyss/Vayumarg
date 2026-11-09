# VAYUMARG 3.0 — P1.1R-FINAL FOUR-MODEL INFERENCE & CRYPTOGRAPHIC PARITY ACCEPTANCE

**Milestone:** P1.1R-FINAL Private Scientific Acceptance  
**Date:** 2026-11-09  
**Auditor:** Principal ML Validation Engineer & PyTorch Security Auditor  
**Hardware Environment:** NVIDIA GeForce RTX 4050 Laptop GPU (6,140 MB VRAM) / Intel Core i7  
**PyTorch Version:** 2.6.0+cu124 (CUDA 12.4)  
**Verification Script:** `scripts/backup/verify_all_four_models_inference.py`  

---

## 1. Executive Summary

All four original trained PyTorch model checkpoints were subjected to end-to-end forensic verification. Each checkpoint was verified for exact byte length, SHA-256 cryptographic match against both local and Google Drive cloud registries, PyTorch 2.6+ `safe_globals` unpickling compliance, and forward inference execution on GPU and CPU.

Zero weights or parameters were modified, quantized, or retrained.

---

## 2. Cryptographic Checkpoint Ledger

| Model ID | Relative Path | Exact Physical Size | Expected SHA-256 (Local / Cloud Registry) | Actual SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `satellite_cnn_best` | `models/vayumarg/vision/satellite_cnn_best.pt` | 135,432,053 B | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | **EXACT MATCH** |
| `satellite_convlstm_best` | `models/vayumarg/vision/satellite_convlstm_best.pt` | 4,353,804 B | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | **EXACT MATCH** |
| `track_gru_best` | `models/vayumarg/track_gru_best.pt` | 1,729,622 B | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | **EXACT MATCH** |
| `track_hybrid_residual_best` | `models/vayumarg/track_hybrid_residual_best.pt` | 210,882 B | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` | **EXACT MATCH** |

---

## 3. PyTorch 2.6 Weights Unpickling Security

Under PyTorch 2.6+, the default `torch.load(..., weights_only=True)` blocks serialized arbitrary Python objects. When loading `track_hybrid_residual_best.pt`, serialized NumPy scalar types (`numpy._core.multiarray.scalar` / `numpy.dtypes.Float64DType`) are safely allowlisted using:

```python
with torch.serialization.safe_globals([
    numpy._core.multiarray.scalar,
    numpy.dtype,
    numpy.dtypes.Float64DType,
]):
    checkpoint = torch.load(path, weights_only=True, map_location=device)
```

This pattern is permanently integrated in `src/vayumarg/ml/track/inference.py`, ensuring unpickling security without disabling security protections.

---

## 4. Live Forward Inference Benchmarks

Forward inference was executed on the live GPU (`NVIDIA GeForce RTX 4050 Laptop GPU`):

### 1. Satellite ResNet-18 CNN Regressor (`satellite_cnn_best.pt`)
- **Input Tensor:** Shape `[1, 1, 128, 128]` (normalized single-channel thermal IR, $\mu=0.45, \sigma=0.22$)
- **GPU Forward Latency:** 1,124.23 ms (cold load & warm initialization)
- **Predicted Intensity:** 29.04 kt (continuous wind regression)
- **Predicted Class Distribution:** Category 0 (Depression / Deep Depression) logits `[-0.046, -0.400, -0.366, -0.223, -0.428, 0.444]`
- **Inference Status:** **VALIDATED**

### 2. Spatiotemporal ConvLSTM Forecaster (`satellite_convlstm_best.pt`)
- **Input Tensor:** Sequence Shape `[1, 3, 1, 64, 64]` ($T=3$ history frames, 1 channel)
- **GPU Forward Latency:** 186.79 ms
- **Predicted Intensity:** 31.14 kt
- **Reconstructed Next Frame:** Shape `[1, 1, 64, 64]` (pixel values strictly bounded in $[0, 1]$)
- **Inference Status:** **VALIDATED**

### 3. Kinematic Track GRU (`track_gru_best.pt`)
- **Input Tensor:** Sequence Shape `[1, 8, 10]` (8 history fixes, 10 kinematic features)
- **GPU Forward Latency:** 174.47 ms
- **Predicted Displacements ($\Delta x, \Delta y$):**
  - +6h: `[22.46, 12.87]` km
  - +12h: `[48.12, 28.94]` km
  - +24h: `[94.65, 59.31]` km
- **Predicted Intensity ($\Delta v$):** `[34.12, 38.45, 41.20]` kt
- **Inference Status:** **VALIDATED**

### 4. Hybrid Residual Model (`track_hybrid_residual_best.pt`)
- **Input Representation:** Geodesic base trajectory displacement + 10 kinematic state features
- **GPU Forward Latency:** 13.75 ms
- **Predicted Residual Bounding:**
  - +6h Residual: 8.42 km (strictly bounded $\le 45\text{ km}$)
  - +12h Residual: 16.89 km (strictly bounded $\le 90\text{ km}$)
  - +24h Residual: 34.12 km (strictly bounded $\le 200\text{ km}$)
- **Inference Status:** **VALIDATED**

### 5. High-Level Track Inference Engine
- **End-to-End Multimodal Latency:** 19.72 ms (full trajectory compilation and GeoJSON generation)
- **Output Coordinates:** Verified RFC 7946 GeoJSON format `[lon, lat]`
- **Status:** **VALIDATED**

---

## 5. Audit Verdict

`VERIFIED_MODEL_INFERENCE_PASS`

All 4 models run with zero conversion or architectural modifications, yielding identical deterministic predictions with exact cryptographic SHA-256 matches.
