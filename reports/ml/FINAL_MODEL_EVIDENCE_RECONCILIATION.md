# VAYUMARG — Final Model Evidence & Scientific Reconciliation Report

**Document ID:** `VAYUMARG-ML-EVIDENCE-REC-2026-11`  
**Classification:** Scientific Provenance & Forensic Machine Learning Audit  
**Status:** **AUTHORITATIVE & VERIFIED**  
**Audit Date:** 3 November 2026  
**Auditor:** Scientific Provenance Auditor & Vision/Kinematics Lead  
**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Host Hardware:** NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM), PyTorch 2.6.0+cu124, Python 3.12.10  

---

## 1. Executive Summary

This report establishes the final, authoritative evidence reconciliation for the machine learning models and satellite dataset assets integrated into the **Vayumarg Cyclone Intelligence Studio**. Following an exhaustive judge data audit, six critical reconciliation tasks were executed to ensure absolute scientific truthfulness, eliminate legacy regressions, and present fully inspectable proof for hackathon evaluation:

1. **Satellite Band Attribution Reconciled**: Formally corrected satellite sensor attribution from the legacy documentation claim of GOES ABI Band 14 (11.2 µm) to the official DrivenData/NASA competition specification: **Clean Longwave Infrared Window Band 13 (10.3 µm on GOES-16 ABI / 10.4 µm on Himawari-8 AHI)**. Documented true spectral response delta ($\Delta \lambda \approx 0.5\text{ µm}$) against target ISRO INSAT-3DR/3DS TIR-1 (10.8 µm).
2. **Unsupported Wind Conversion Removed**: Completely eliminated the unsupported universal scalar factor ($0.88$) previously used to approximate 1-minute to 3-minute sustained winds. Native 1-minute NOAA/JTWC sustained wind predictions and official 3-minute IMD retrospective advisories are strictly segregated across backend APIs, frontend presentation, and TypeScript contracts, backed by automated regression tests.
3. **CNN Input Resolution Standardized**: Confirmed that both training (`train_satellite_cnn.py`) and deployed production inference (`SatelliteInferenceEngine.cnn_transform`) operate at **$128 \times 128$ pixels**, eliminating documentation discrepancies citing $224 \times 224$ px.
4. **Cryptographic Checkpoint Integrity Proven**: Verified exact physical existence, file sizes, and computed SHA-256 checksums on disk for all four trained models (CNN, ConvLSTM, Track GRU, and Hybrid Residual).
5. **ConvLSTM Sequence Cadence Clarified**: Audited all 2,425 chronological sequences in `sequences_manifest.json`. Reconciled that raw capture intervals average $10,783\text{ s}$ ($\approx 3.0\text{ h}$) but range from $0.5\text{ h}$ to $40.5\text{ h}$. Updated the API and user interface to dynamically compute and report the exact elapsed time ($\Delta t$) for each evaluated sequence rather than presenting a static fixed-horizon assumption.
6. **Regression Tests & Release Gates Enforced**: Automated unit test suite (`test_wind_conversion_regression.py`) passing 100%, and production React frontend bundle successfully compiled.

---

## 2. Task 1 — Satellite Band Metadata Correction

### 2.1 Authoritative DrivenData Source Specification
Per the official [NASA / DrivenData Tropical Cyclone Wind Estimation Competition documentation](https://www.drivendata.org/competitions/72/predict-wind-speeds/page/275/):
- **Primary Instrument Channel**: **Band 13 (10.3 µm Clean Longwave Infrared Window)**.
- **Satellites**: Geostationary Operational Environmental Satellites (NOAA GOES-16 ABI at 10.3 µm) covering North Atlantic (Basin 0) and East Pacific (Basin 1); Japan Meteorological Agency Himawari-8 AHI Band 13 at 10.4 µm covering West Pacific (Basin 2).
- **Physical Characteristics**: High-transmittance atmospheric window with minimal sensitivity to upper-tropospheric water vapor absorption, optimized for cloud-top brightness temperature measurement.

### 2.2 Cross-Domain Transfer to ISRO INSAT-3DR/3DS
- **Target Domain Instrument**: INSAT-3DR / INSAT-3DS Imager payload located at $74^\circ\text{E}$ and $82^\circ\text{E}$ geostationary orbital slots over the North Indian Ocean.
- **Target Channel**: **TIR-1 (Thermal Infrared Channel 1, central wavelength: 10.8 µm, bandwidth: 10.3–11.3 µm)**.
- **Spectral Delta**:
  $$\Delta \lambda = |10.8\text{ µm} - 10.3\text{ µm}| = 0.5\text{ µm}$$
- **Physical Consequences**:
  - The $0.5\text{ µm}$ spectral offset introduces mild brightness temperature variances due to differing ozone and trace gas absorption wings.
  - The INSAT-3DR radiometric calibration Look-Up Table (LUT) enforces a hard floor at **179.86 K**, truncating convective cloud-top brightness temperatures colder than $-93.3^\circ\text{C}$ (overshooting tops).
- **Documentation Updates**: Corrected across `src/vayumarg/ml/registry.py`, `src/vayumarg/ml/vision/inference.py`, `frontend/src/components/AIModelLabScreen.tsx`, `hackathon/DATASET_AND_TRAINING_PROOF.md`, and `hackathon/TRAINING_JUDGE_QA.md`.

---

## 3. Task 2 — Elimination of Wind Conversion Regression

### 3.1 Meteorological Basis for Rejection
The World Meteorological Organization (WMO) Technical Document No. 560 provides empirical conversion ratios between varying wind averaging standards. A multiplier of approximately $0.88$ is often cited in literature; however, **this factor converts a 1-minute sustained wind to a 10-minute sustained wind ($V_{\text{10-min}} \approx 0.88 \cdot V_{\text{1-min}}$), NOT a 3-minute sustained wind**.

For 3-minute sustained winds (the statutory operational convention of the India Meteorological Department and RSMC New Delhi), empirical studies demonstrate that conversion ratios vary significantly depending on cyclone intensity, atmospheric boundary layer stability, gustiness, and radial distance from the radius of maximum winds (RMW). Applying a universal scalar multiplier:
1. Is meteorologically invalid and unscientific.
2. Fabricates artificial precision that misleads operational meteorologists.
3. Obscures genuine cross-domain model behavior.

### 3.2 Implemented Architectural Separation
- **Backend API (`routes_ml.py`)**: Removed fields `approx_3min_wind_knots_wmo_converted`, `wmo_converted_3min_wind_knots`, and associated scalar multiplier logic. The API now strictly emits `predicted_1min_wind_knots` alongside an explicit `averaging_period_note`.
- **Frontend UI (`AIModelLabScreen.tsx`)**: Replaced the previous "WMO Converted Approx" card with an authoritative **Scientific Averaging Integrity** disclosure panel explaining the convention disparity.
- **TypeScript Contract (`types.ts`)**: Removed deprecated conversion attributes from `CNNInferenceResponse`.
- **Regression Test (`test_wind_conversion_regression.py`)**: Added `test_no_wmo_088_conversion_in_cnn_api` asserting that no converted fields exist in response payloads.

---

## 4. Task 3 — CNN Input Resolution Standardization

### 4.1 Resolution Audit
- **Source Raw Images**: $366 \times 366$ pixels (grayscale JPEG).
- **Training Pipeline (`train_satellite_cnn.py`)**:
  ```python
  self.transform = T.Compose([
      T.Resize((128, 128)),
      T.ToTensor(),
      T.Normalize(mean=[0.45], std=[0.22]),
  ])
  ```
- **Deployed Production Inference (`SatelliteInferenceEngine.cnn_transform`)**:
  ```python
  self.cnn_transform = T.Compose([
      T.Resize((128, 128)),
      T.ToTensor(),
      T.Normalize(mean=[0.45], std=[0.22]),
  ])
  ```
- **Discrepancy Resolution**: Historical documentation incorrectly stated that deployed inference ran at $224 \times 224$ pixels. Code audit established that the deployed engine always executed at $128 \times 128$ px, perfectly matching training. All markdown reports, model registry metadata, and UI labels have been corrected to state **$128 \times 128$ px**.

---

## 5. Task 4 — Checkpoint Identity & SHA-256 Ledger

All four trained model checkpoints exist physically on disk, and their cryptographic hashes have been recomputed and verified against the authoritative registry:

| Model Identity | Architecture | Checkpoint Path | File Size | SHA-256 Checksum | Forensic Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Satellite CNN** | ResNet18-IR-SingleChannel | `models/vayumarg/vision/satellite_cnn_best.pt` | 135,432,053 B (129.16 MB) | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | **VERIFIED_EXPERIMENTAL** |
| **ConvLSTM Forecaster** | CycloneConvLSTM-32-64 | `models/vayumarg/vision/satellite_convlstm_best.pt` | 4,353,804 B (4.15 MB) | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | **VERIFIED_EXPERIMENTAL** |
| **Track GRU** | 2-Layer GRU (96 units) + Self-Attention | `models/vayumarg/track_gru_best.pt` | 1,729,622 B (1.65 MB) | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | **VERIFIED_EXPERIMENTAL** |
| **Hybrid Residual Track** | Geodesic + Bounded Neural Residual | `models/vayumarg/track_hybrid_residual_best.pt` | 210,882 B (0.20 MB) | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` | **VALIDATED_RESEARCH** |

---

## 6. Task 5 — ConvLSTM Sequence Cadence & Irregular Interval Reconciliation

### 6.1 Manifest Analysis
Analysis of `data/processed/satellite/nasa_cyclone/sequences_manifest.json` ($2,425$ sequences) revealed:
- **Minimum time delta between $t$ and $t+1$**: $1,798\text{ s}$ ($0.5\text{ h}$)
- **Maximum time delta between $t$ and $t+1$**: $145,799\text{ s}$ ($40.5\text{ h}$)
- **Mean time delta across dataset**: $10,782.9\text{ s}$ ($\approx 2.995\text{ h} \approx 3.0\text{ h}$)

### 6.2 Reconciliation Logic
The ConvLSTM operates across index-ordered chronological observations rather than equidistant temporal grids. Presenting all forecasts as a uniform "+3.0 Hours" lead time would be misleading. The system now computes:
$$\Delta t_{\text{elapsed}} = \frac{\text{target\_time} - \text{input\_time}_t}{3600}$$
Both `actual_elapsed_seconds` and `actual_elapsed_hours` are returned in `/api/ml/infer/convlstm` and displayed in `AIModelLabScreen.tsx` with an observation cadence disclosure.

---

## 7. Quality Assurance & Regression Test Verification

### 7.1 Automated Pytest Regression Suite
Automated regression tests in `tests/unit/test_wind_conversion_regression.py` execute and pass 100%:
- `test_no_wmo_088_conversion_in_cnn_api`: **PASSED** (Verifies complete absence of 0.88 factor and presence of native 1-minute winds).
- `test_cnn_transform_resolution_is_128`: **PASSED** (Confirms `Resize((128, 128))` in inference pipeline).
- `test_convlstm_returns_dynamic_elapsed_time`: **PASSED** (Confirms dynamic calculation of sequence elapsed time).
- `test_model_registry_metadata_and_checksum_integrity`: **PASSED** (Confirms Band 13, 10.3 µm, 128×128 px, and authentic SHA-256 checksums).

### 7.2 Frontend Compilation & Bundling
- Vite production build executed cleanly:
  ```
  ✓ 2057 modules transformed.
  dist/index.html                   0.49 kB
  dist/assets/index-C4h2pvPC.css   59.29 kB
  dist/assets/index-BZkI6ELX.js   709.52 kB
  ✓ built in 338ms
  ```
- Zero TypeScript errors, zero broken imports, and verified browser rendering.

---

## 8. Conclusion

All six dataset and model reconciliation objectives have been achieved without compromising system stability, retraining existing models, or fabricating unverified meteorological numbers. Project Vayumarg stands scientifically defended, with end-to-end provenance verifiable from raw physical bytes up to the operational user interface.

