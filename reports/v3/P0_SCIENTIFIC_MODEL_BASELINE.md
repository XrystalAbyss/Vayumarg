# VAYUMARG 3.0 — P0 SCIENTIFIC MODEL BASELINE FORENSICS

**Audit Date:** 7 November 2026  
**Auditor:** Machine Learning Research Engineer & Principal Tropical Cyclone Meteorologist  
**Classification:** Model Forensics, Benchmark Integrity & Credibility Appraisal  
**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Host Hardware:** NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM), PyTorch 2.6.0+cu124  

---

## 1. Executive Summary

This report delivers a forensic audit of the four machine learning and deterministic models implemented in Vayumarg. Checkpoint hashes, physical parameter counts, training logs, evaluation ledgers, and inference behaviors were independently confirmed. 

A central conclusion of this scientific review is that **several promotional hackathon claims regarding AI superiority over physics are invalid**:
1. In track forecasting, **the deterministic geodesic constant-velocity baseline beats the neural Track GRU across every forecast horizon** (+6h, +12h, +24h).
2. In short-range intensity forecasting, **the naive persistence baseline ($y_{t+1} = y_t$) outperforms the Spatiotemporal ConvLSTM by a factor of 9** (1.90 kt MAE vs 17.20 kt MAE).
3. The hybrid residual model was engineered after inspecting test-set error patterns; its reported gains must be classified as **exploratory research** until validated on a clean, unseen confirmatory cohort.
4. On authentic INSAT satellite imagery, the single-frame ResNet-18 model fails to preserve the true operational ranking between AMPHAN and BIPARJOY, demonstrating significant cross-sensor domain shift.

---

## 2. Checkpoint Ledger & Physical Provenance

All four model checkpoints physically exist in `models/vayumarg/` and match their computed SHA-256 hashes:

| Model ID | Checkpoint File | Physical Bytes | SHA-256 Digest | Parameter Count |
| :--- | :--- | :--- | :--- | :--- |
| **`satellite_cnn`** | `models/vayumarg/vision/satellite_cnn_best.pt` | 135,432,053 B (129.16 MB) | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | 11,273,543 |
| **`convlstm`** | `models/vayumarg/vision/satellite_convlstm_best.pt` | 4,353,804 B (4.15 MB) | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | 362,017 |
| **`track_gru`** | `models/vayumarg/track_gru_best.pt` | 1,729,622 B (1.65 MB) | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | 141,802 |
| **`track_hybrid_residual`** | `models/vayumarg/track_hybrid_residual_best.pt` | 210,882 B (0.20 MB) | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` | 50,282 |

---

## 3. Detailed Forensic Assessment of Models

### 3.1 Model 1: ResNet-18 Satellite Intensity Regressor (`satellite_cnn`)
- **Architecture:** ResNet-18 backbone initialized with ImageNet weights (3-channel `conv1` averaged to 1-channel stem: $\mathbf{W}_{\text{IR}} = \frac{1}{3}\sum \mathbf{W}_{\text{RGB}}$). Features 512-dim adaptive pooling followed by two parallel heads:
  - Regression Head: `512 -> 128 -> 32 -> 1` (continuous wind speed in knots).
  - Classification Head: `512 -> 64 -> 6` (probability distribution over 6 source-native wind bins: $<28, 28\text{--}33, 34\text{--}47, 48\text{--}63, 64\text{--}89, \ge 90\text{ kt}$).
- **Training Setup:** 15 epochs on NVIDIA RTX 4050 GPU (71.35 seconds pure fit time). Smooth L1 loss ($\beta=2.0$) + $0.1 \times$ Cross-Entropy loss.
- **Source-Domain Benchmark Metrics (414 Held-Out Test Frames across 5 Unseen Storms):**
  - Mean Absolute Error (MAE): **10.00 knots**
  - Root Mean Squared Error (RMSE): **14.26 knots**
  - Pearson Correlation Coefficient ($r$): **0.8642**
  - Category Classification Accuracy: **45.17%** (within 1 category: **88.65%**)
- **Zero-Shot Cross-Domain Transfer on Authentic INSAT Crops:**
  - **AMPHAN:** Predicted **76.1 kt** vs 95.0 kt IMD retrospective target ($\Delta = -18.9\text{ kt}$). Dual-head conflict: Classification head predicted Bin 5 ($\ge 90\text{ kt}$, 58.9% prob), while regression head predicted 76.1 kt (Bin 4).
  - **BIPARJOY:** Predicted **80.3 kt** vs 85.0 kt IMD retrospective target ($\Delta = -4.7\text{ kt}$).
  - **REMAL:** Predicted **46.9 kt** vs 60.0 kt IMD retrospective target ($\Delta = -13.1\text{ kt}$).
  - **DANA:** Predicted **35.6 kt** (Correctly marked `INELIGIBLE` for primary IMD evaluation).
  - **Ranking Inversion:** The model predicted higher intensity for BIPARJOY (80.3 kt) than for AMPHAN (76.1 kt), despite AMPHAN being an Extremely Severe / Super Cyclonic system with substantially higher physical kinetic energy.
- **Root Cause of Transfer Gap:**
  1. Spectral delta ($\lambda = 10.3\text{ µm}$ in training vs $10.8\text{ µm}$ in INSAT-3DR).
  2. Radiometric LUT floor in INSAT ($179.86\text{ K}$) truncating AMPHAN's deep convective core.
  3. Averaging period discrepancy (1-minute NOAA label vs 3-minute IMD target).

---

### 3.2 Model 2: Spatiotemporal ConvLSTM Forecaster (`convlstm`)
- **Architecture:** 2-Layer ConvLSTM (32 filters $\to$ 64 filters, $3 \times 3$ kernels) taking $T=3$ sequential frames ($64 \times 64\text{ px}$) + Convolutional Decoder ($64 \to 32 \to 1$) for next-frame visual reconstruction + Dense Head for scalar intensity regression.
- **Training Setup:** 12 epochs on RTX 4050 (182.08 seconds pure fit time). Combined pixel MSE reconstruction loss + Smooth L1 intensity loss.
- **Test-Set Benchmark Results (399 Held-Out Sequences across 5 Unseen Storms):**

| Benchmark / Model | Next-Frame Pixel MSE | Skill vs Persistence | Intensity Test MAE | Intensity Test RMSE |
| :--- | :--- | :--- | :--- | :--- |
| **Last-Frame Persistence Baseline** | 0.01328 | 0.0% (Reference) | **1.90 kt** | **3.23 kt** |
| **Spatiotemporal ConvLSTM** | **0.01084** | **+18.35%** | **17.20 kt** | **23.72 kt** |

- **Scientific Reality & Explanation:**
  - **Visual Kinematics:** ConvLSTM demonstrates genuine physical skill (+18.35%) in reconstructing cloud canopy advection and eyewall curvature.
  - **Scalar Intensity Failure:** For scalar intensity regression, ConvLSTM is mathematically inferior to the trivial persistence baseline by 15.3 knots. Tropical cyclones change intensity slowly over 1–3 hours ($\approx 1\text{--}2\text{ kt/h}$); predicting no change ($\hat{y}_{t+1} = y_t$) achieves 1.90 kt MAE. ConvLSTM, downsampled to $64 \times 64$ pixels, lost the fine radial eye-wall gradient features needed to distinguish fine intensity variations.
  - **Conclusion:** ConvLSTM should be positioned solely as a convective cloud-shield kinematics predictor, not an intensity forecaster.

---

### 3.3 Model 3: Recurrent Track Forecaster (`track_gru`)
- **Architecture:** 2-Layer Gated Recurrent Unit (96 hidden units) + Temporal Self-Attention pooling across past $T=8$ 3-hourly coordinate fixes (24-hour history) + Linear projection heads for displacements ($\Delta x, \Delta y$ in km) and future wind at +6h, +12h, and +24h.
- **Training Setup:** 25 epochs on North Indian Ocean IBTrACS (331 train storms, 70 val storms, 72 test storms; 25.7 seconds fit time).
- **Test-Set Benchmark Results (1,216 Held-Out Sequence Windows from 51 Active Storms):**

| Forecast Horizon | Stationary Baseline Error | Geodesic Constant-Velocity Error | Pure Track GRU Error | GRU Skill vs Geodesic | GRU Skill vs Stationary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **+6 Hours** | 97.5 km | **35.3 km** | 42.2 km | **-19.4%** | +56.7% |
| **+12 Hours** | 193.8 km | **78.3 km** | 89.8 km | **-14.7%** | +53.7% |
| **+24 Hours** | 388.5 km | **180.5 km** | 239.3 km | **-32.6%** | +38.4% |

- **Scientific Reality & Explanation:**
  - Track GRU significantly outperforms a stationary assumption (+56.7% at +6h), proving it learned forward translation.
  - However, **the deterministic Geodesic baseline beats Track GRU across all horizons** (+6h by 6.9 km; +12h by 11.5 km; +24h by 58.8 km).
  - Atmospheric steering currents exhibit strong physical momentum over 6–24 hours. A neural network trained purely on coordinate sequences without environmental wind fields (e.g., 500 hPa geopotential height, 850 hPa steering winds) tends to predict mean climatological recurvature, degrading accuracy relative to pure linear momentum.

---

### 3.4 Model 4: Geodesic-Neural Hybrid Residual Forecaster (`track_hybrid_residual`)
- **Architecture:** Deterministic geodesic constant-velocity projection serves as the physical backbone; a lightweight neural residual network (50,282 parameters) predicts bounded differential corrections ($\delta x, \delta y$) bounded by a hyperbolic tangent function:
  $$\hat{\mathbf{x}}(t + \Delta t) = \mathbf{x}_{\text{geodesic}}(t + \Delta t) + \mathbf{r}_{\text{neural}}(H_{0:t})$$
- **Reported Benchmark Performance on Historical Test Set:**
  - +6h Track Error: **33.3 km** (+5.7% skill vs geodesic)
  - +12h Track Error: **70.6 km** (+9.8% skill vs geodesic)
  - +24h Track Error: **158.1 km** (+12.4% skill vs geodesic)
- **Methodological Qualification & Status:**
  - **Risk:** This architecture was devised and evaluated on the same held-out test partition used to diagnose Track GRU failures during the hackathon sprint.
  - **Status:** **`IMPLEMENTED_EXPERIMENTAL` (Exploratory Research Only)**.
  - It must not be cited as an established scientific improvement until validated against a strictly sequestered, independent confirmatory cohort (e.g., historical storms from 2021–2024 held back completely from architectural exploration).

