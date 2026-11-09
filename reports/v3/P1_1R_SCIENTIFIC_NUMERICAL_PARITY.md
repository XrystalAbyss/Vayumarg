# VAYUMARG 3.0 — P1.1R SCIENTIFIC NUMERICAL PARITY REPORT

## 1. Executive Summary

Milestone P1.1R executed a deterministic scientific numerical parity suite (`scripts/backup/verify_scientific_numerical_parity.py`) covering 13 core meteorological, kinematic, radiometric, and machine learning invariants. 

All 13 checks passed with zero numerical regressions, confirming that refactoring did not alter any scientific calculation or model behavior.

---

## 2. Invariant Verification Table (13 Items)

| Item # | Verification Invariant | Baseline Value | Modular Post-Refactor Value | Residual / Diff | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | Geodesic Extrapolation (+6h) | Lat: 18.5999°, Lon: 67.9005° | Lat: 18.5999°, Lon: 67.9005° | 0.0000° | **PASS** |
| **2** | Geodesic Extrapolation (+12h) | Lat: 18.9997°, Lon: 68.1019° | Lat: 18.9997°, Lon: 68.1019° | 0.0000° | **PASS** |
| **3** | Geodesic Extrapolation (+24h) | Lat: 19.7985°, Lon: 68.5076° | Lat: 19.7985°, Lon: 68.5076° | 0.0000° | **PASS** |
| **4** | Spherical Haversine Metric | 56.590000 km (rounded) | 56.591468 km (exact) | 0.001468 km | **PASS** |
| **5** | North Indian Ocean Radius | $R = 6371.0\text{ km}$ | $R = 6371.0\text{ km}$ | Exact Match | **PASS** |
| **6** | Strict Predictive Leakage Shield | 0 post-issue fixes in input | 0 post-issue fixes in input | 0 fixes leaked | **PASS** |
| **7** | Satellite Crop Valid Pixels | 40,401 / 40,401 | 40,401 / 40,401 | 0 missing | **PASS** |
| **8** | Radiometric LUT Calibration Floor | $\ge 179.80\text{ K}$ | $179.86\text{ K}$ | Invariant held | **PASS** |
| **9** | TIR-1 PNG Visual Rendering | 59,387 bytes | 59,387 bytes | 0 byte diff | **PASS** |
| **10** | Track GRU Model Forward Pass | +6h: [19.04, 67.47] | +6h: [19.04, 67.47] | Exact Match | **PASS** |
| **11** | Hybrid Residual Model Pass | +6h: [18.91, 67.47] | +6h: [18.91, 67.47] | Exact Match | **PASS** |
| **12** | ResNet-18 IR Forward Output | Wind: 28.8818 kt (seed 42) | Wind: 28.8818 kt (seed 42) | Exact Match | **PASS** |
| **13** | ConvLSTM Spatiotemporal Pass | Wind: 31.7294 kt (seed 42) | Wind: 31.7294 kt (seed 42) | Exact Match | **PASS** |

---

## 3. Scientific Mathematical Evidence

### Geodesic Kinematic Formulas
Extrapolation uses Great-Circle forward velocity from pre-issue fixes $(t \le t_{\text{issue}})$:
$$\Delta \phi = \frac{v_y \cdot \Delta t}{111.12}, \quad \Delta \lambda = \frac{v_x \cdot \Delta t}{111.12 \cdot \cos(\phi_{\text{ref}})}$$
- Tested Landmark: Cyclone BIPARJOY at issue time `2023-06-11 06:00:00Z`.
- Observations strictly partitioned: 51 historical fixes ($t \le t_{\text{issue}}$) selected, 0 future fixes admitted into forecast calculation.
- Geodesic coordinates match baseline to within $< 10^{-4}$ degrees across all three lead times.

### Radiometric Integrity
- File: `data/processed/satellite/crops/BIPARJOY_20230612_2358_MULTICHANNEL.h5`.
- Minimum brightness temperature measured: `179.86 K`, respecting the ISRO INSAT-3D lookup table physical boundary (`179.80 K`).
- Cold cloud fraction ($T < 200\text{ K}$): `0.2438` (24.38% deep convective core coverage).

### ML Model Reproducibility
- All 4 model checkpoints (`satellite_cnn_best.pt`, `satellite_convlstm_best.pt`, `track_gru_best.pt`, `track_hybrid_residual_best.pt`) execute with weights-only security.
- Under fixed pseudo-random generator state (`torch.manual_seed(42)`), ResNet-18 predicts `28.8818 kt` wind speed and ConvLSTM predicts `31.7294 kt` wind speed with identical next-frame tensor geometry `(1, 1, 64, 64)`.

