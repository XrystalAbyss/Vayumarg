# VAYUMARG 3.0 — P1.1 SCIENTIFIC EVIDENCE CORRECTION REPORT

**Audit Date:** 2026-11-07  
**Auditor:** Cyclone Forecast Verification Researcher & Scientific Data Auditor  
**Classification:** Scientific Benchmark Provenance & Empirical Ledger Audit  
**Status:** COMPLETE & INDEPENDENTLY RECONCILED  

---

## 1. Executive Summary & Root Cause Analysis

A discrepancies audit was conducted on the performance figures reported in the repository's public documentation versus the actual saved machine-learning evaluation ledgers:

### The Discrepancy:
* **Published README Claim:**
  * Track GRU achieves:
    * +6h: 42.1 km MAE
    * +12h: 84.7 km MAE
    * +24h: 168.3 km MAE
* **Empirical Ground-Truth Ledger (`docs/evidence/hybrid_track_evaluation_summary.json`):**
  * Pure Track GRU (`checkpoint_gru_sha256: 24d4788f...`):
    * +6h: **42.19 km Mean MAE** (36.00 km median, 50.77 km RMSE)
    * +12h: **89.77 km Mean MAE** (77.50 km median, 105.49 km RMSE)
    * +24h: **239.35 km Mean MAE** (217.93 km median, 276.14 km RMSE)

### Root Cause:
1. **Unverified Linear Extrapolation:** The figures `42.1 km -> 84.7 km -> 168.3 km` represent an improvised linear doubling ($42.1 \times 2 \approx 84.7$; $84.7 \times 2 \approx 168.3$) authored during the hackathon phase.
2. **Obscuring Model Physics & Degradation:** Pure GRU models unconstrained by physical boundary conditions suffer from error compounding over longer horizons. By +24h, Pure GRU mean track error degrades to **239.35 km**, which is significantly worse than a simple great-circle geodesic baseline (**180.49 km**).
3. **Scientific Value of Hybrid Architecture:** By fabricating a linear 168.3 km number for pure GRU, the documentation obscured the exact scientific justification for developing the **Hybrid Residual Model**, which anchors predictions to the geodesic trajectory and learns bounded residual displacements, achieving **158.06 km MAE** (+24h).

---

## 2. Authoritative Multi-Horizon Track Benchmarks

All metrics below are derived directly from `docs/evidence/hybrid_track_evaluation_summary.json` evaluated across **1,216 test sliding windows** from **51 active test storms** (out of 72 allocated test storms) in the NOAA IBTrACS v04r01 North Indian Ocean basin (1982–2024):

| Forecast Horizon | Evaluation Model | Mean MAE (km) | Median MAE (km) | RMSE (km) | Skill vs Stationary (%) | Skill vs Geodesic (%) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **+6h** | Stationary Baseline | 97.51 | — | — | — | — |
| | Geodesic Kinematic Base | 35.32 | 30.15 | 48.24 | 63.78% | — |
| | Pure Track GRU | 42.19 | 36.00 | 50.77 | 56.73% | -19.45% |
| | **Hybrid Residual Model** | **33.31** | **26.93** | **44.19** | **65.84%** | **+5.71%** |
| **+12h** | Stationary Baseline | 193.84 | — | — | — | — |
| | Geodesic Kinematic Base | 78.27 | 66.42 | 98.70 | 59.62% | — |
| | Pure Track GRU | 89.77 | 77.50 | 105.49 | 53.69% | -14.69% |
| | **Hybrid Residual Model** | **70.62** | **60.28** | **87.45** | **63.57%** | **+9.78%** |
| **+24h** | Stationary Baseline | 388.47 | — | — | — | — |
| | Geodesic Kinematic Base | 180.49 | 156.74 | 218.19 | 53.54% | — |
| | Pure Track GRU | 239.35 | 217.93 | 276.14 | 38.39% | -32.61% |
| | **Hybrid Residual Model** | **158.06** | **138.96** | **189.35** | **59.31%** | **+12.43%** |

---

## 3. Clustered Bootstrap Significance Analysis

To confirm that the Hybrid Forecaster's improvement over the Geodesic baseline is statistically significant and not an artifact of specific storm tracks, 1,000 storm-clustered bootstrap iterations were computed:

* **+6h Horizon:** Mean improvement: **2.02 km** (5.71% skill).  
  **95% Confidence Interval:** `[0.88 km, 3.30 km]` (strictly $> 0$, statistically significant).
* **+12h Horizon:** Mean improvement: **7.65 km** (9.78% skill).  
  **95% Confidence Interval:** `[4.61 km, 10.91 km]` (strictly $> 0$, statistically significant).
* **+24h Horizon:** Mean improvement: **22.43 km** (12.43% skill).  
  **95% Confidence Interval:** `[15.04 km, 29.76 km]` (strictly $> 0$, statistically significant).

---

## 4. Module A Remote Sensing & Vision Evidence Audit

### 4.1 ResNet-18 IR Single-Frame Regressor (`docs/evidence/cnn_held_out_evidence.json`)
* **Cohort:** 414 test frames across 5 unseen held-out storms (`xtd`, `gme`, `dzw`, `hig`, `qpq`).
* **Performance:**
  * Mean Absolute Error: **10.00 knots**
  * Root Mean Square Error: **14.26 knots**
  * Pearson Correlation Coefficient: **$r = 0.8642$**
* **Wind Standard:** NOAA/JTWC 1-minute maximum sustained wind (knots) from NASA competition labels.
* **Intensity Stratification:**
  * $< 28\text{ kt}$: 3.68 kt MAE
  * $28 - 33\text{ kt}$: 5.11 kt MAE
  * $34 - 47\text{ kt}$: 10.33 kt MAE
  * $48 - 63\text{ kt}$: 8.52 kt MAE
  * $64 - 89\text{ kt}$: 15.64 kt MAE
  * $\ge 90\text{ kt}$: 13.67 kt MAE

### 4.2 ConvLSTM Spatiotemporal Forecaster (`docs/evidence/convlstm_held_out_evidence.json`)
* **Cohort:** 399 chronological sequences ($T=3$) across 5 unseen storms.
* **Next-Frame Image Extrapolation:**
  * ConvLSTM Reconstruction MSE: **0.01084**
  * Frame Persistence MSE: **0.01328**
  * **Skill Score vs Persistence:** **+18.35%** in visual structural tracking.
* **Intensity Head Comparison:**
  * ConvLSTM Intensity MAE: **17.20 kt**
  * Frame Intensity Persistence: **1.90 kt**
  * Single-Frame ResNet-18 Regressor: **10.00 kt**
  * **Physical Conclusion:** The recurrent convolutional downscaling to $64 \times 64$ pixels smooths sharp eye-wall temperature gradients necessary for precise peak wind regression. The model excels at cloud field translation (+18.35%), but intensity estimation is better served by high-resolution single-frame regression ($128 \times 128$) or short-range persistence.

---

## 5. Public Documentation Correction

`README.md` has been updated with these exact empirical tables, confidence intervals, and physical qualifications, establishing complete transparency for scientific peers and evaluators.

