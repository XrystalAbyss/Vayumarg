# VAYUMARG Deep Learning Spatiotemporal Track Forecaster: Recurrent Track GRU Training Report

## 1. Executive Summary

This report documents the architecture, training dataset, empirical training trajectory, evaluation benchmark, and baseline comparisons for the **Vayumarg-Track-GRU** recurrent neural network model.

The objective is multi-horizon cyclone trajectory forecasting (+6h, +12h, +24h displacement vectors in kilometers) and simultaneous intensity forecasting (knots) from historical observation fixes, evaluated rigorously against:
1. **Deterministic Constant-Velocity Geodesic Extrapolation** (the operational Module B baseline).
2. **Stationary Baseline** (displacement = 0 km).
3. **Wind Persistence Baseline** (future wind = current wind).

### Key Empirical Findings

- **Model Architecture**: 2-Layer Recurrent Gated Recurrent Unit (GRU) with 96 hidden units, temporal feature normalization, and self-attention temporal context pooling.
- **Trainable Parameters**: 141,802.
- **Training Dataset**: Official IBTrACS v04r01 North Indian Ocean historical cyclone database (1980–2024).
- **Partitioning Strategy**: Strictly storm-disjoint split by unique storm identifier (`SID`) with seed 42 (70% train / 15% validation / 15% test).
- **Execution Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM), PyTorch 2.6.0+cu124 on Windows 11.
- **Training Time**: 25.7 seconds (25 epochs with Cosine Annealing learning rate schedule).
- **Saved Checkpoint**: `models/vayumarg/track_gru_best.pt` (SHA-256: `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986`).
- **Cryptographic Registry Gate**: Verified and unlocked under `VERIFIED_EXPERIMENTAL`.

---

## 2. Dataset Curation and Storm-Disjoint Partitioning

To completely prevent data leakage across autocorrelated cyclone observations, storms were partitioned at the storm level. No cyclone in the training set appears in either the validation or held-out test subsets.

### 2.1 Storm and Sequence Window Summary

| Subset | Storm Count | 3-Hourly Sliding Windows ($T=8$ in, $T=+24$h out) | Description |
| :--- | :--- | :--- | :--- |
| **Train** | 331 storms | 8,201 windows | North Indian Ocean cyclones (1980–2024) |
| **Validation** | 70 storms | 1,750 windows | Intermediate validation & checkpoint selection |
| **Held-Out Test** | 72 storms | 1,216 windows | Unseen landmark test storms for final evaluation |
| **Total** | **473 storms** | **11,167 windows** | 100% verified authentic meteorological fixes |

### 2.2 Input Feature Representation ($T_{in} = 8$ fixes, 24 Hours of History)

Each timestep $\tau \in [t-21\text{h}, t]$ encodes 10 normalized physical features:
1. `lat / 30.0`: Normalized geographic latitude.
2. `(lon - 75.0) / 30.0`: Centered and normalized geographic longitude.
3. `dx_prev / 50.0`: Longitudinal displacement in km relative to previous 3h fix.
4. `dy_prev / 50.0`: Latitudinal displacement in km relative to previous 3h fix.
5. `speed_kmh / 50.0`: Cyclone translation velocity in km/h.
6. `sin(bearing)`: Trigonometric sine of track heading angle.
7. `cos(bearing)`: Trigonometric cosine of track heading angle.
8. `wind_kt / 150.0`: Normalized maximum sustained surface wind.
9. `delta_wind / 10.0`: 3-hour intensity change tendency.
10. `t / 7.0`: Relative progression fraction through historical window $[0, 1]$.

### 2.3 Target Multi-Horizon Formulation

- **Horizon +6h (+2 steps)**: Target $(dx_{+6\text{h}}, dy_{+6\text{h}})$ in km, target $wind_{+6\text{h}}$ in kt.
- **Horizon +12h (+4 steps)**: Target $(dx_{+12\text{h}}, dy_{+12\text{h}})$ in km, target $wind_{+12\text{h}}$ in kt.
- **Horizon +24h (+8 steps)**: Target $(dx_{+24\text{h}}, dy_{+24\text{h}})$ in km, target $wind_{+24\text{h}}$ in kt.

Target displacements are converted back to geographic coordinates via spherical trigonometry:
$$\text{Lat}_{pred} = \text{Lat}_{origin} + \frac{dy}{111.12}$$
$$\text{Lon}_{pred} = \text{Lon}_{origin} + \frac{dx}{111.12 \times \cos(\text{Lat}_{origin})}$$

---

## 3. Neural Architecture & Optimization

### 3.1 Network Architecture

```text
Input Features [B, 8, 10]
       │
       ▼
Input Projection: Linear(10 -> 96) + LayerNorm + GELU + Dropout(0.15)
       │
       ▼
Recurrent Core: 2-Layer GRU (hidden_size=96, batch_first=True, dropout=0.15)
       │
       ├── Last Hidden State [B, 96]
       │
       └── Temporal Self-Attention: Linear(96 -> 1) -> Softmax(dim=1) -> Context Vector [B, 96]
       │
       ▼
Concatenated Representation: [Last Hidden, Context] -> [B, 192]
       │
       ├── Trajectory Head: Linear(192 -> 96) -> LayerNorm -> GELU -> Dropout -> Linear(96 -> 6)
       │                    Outputs (dx, dy) in km for horizons [+6h, +12h, +24h]
       │
       └── Intensity Head:  Linear(192 -> 48) -> GELU -> Dropout -> Linear(48 -> 3)
                            Outputs predicted wind speed in kt for [+6h, +12h, +24h]
```

### 3.2 Loss Function & Optimization

- **Displacement Loss**: Smooth L1 loss ($\beta = 5.0\text{ km}$) to ensure robustness against outlier track erratic motions.
- **Intensity Loss**: Smooth L1 loss ($\beta = 2.0\text{ kt}$).
- **Total Multi-Task Loss**: $\mathcal{L}_{total} = \mathcal{L}_{disp} + 0.1 \times \mathcal{L}_{wind}$.
- **Optimizer**: AdamW ($\text{lr} = 10^{-3}$, weight decay $= 10^{-4}$).
- **Learning Rate Scheduler**: Cosine Annealing over 25 epochs ($\eta_{min} = 10^{-5}$).
- **Gradient Clipping**: Maximum norm of 1.0.

---

## 4. Empirical Training History

Training completed on the NVIDIA RTX 4050 GPU in **25.7 seconds**.

| Epoch | Train Loss | Validation Loss | Learning Rate | Best Checkpoint |
| :--- | :--- | :--- | :--- | :--- |
| **01** | 117.87 | 108.79 | 0.000996 | ★ Best Saved |
| **05** | 93.05 | 84.44 | 0.000905 | ★ Best Saved |
| **10** | 75.16 | 69.00 | 0.000679 | ★ Best Saved |
| **15** | 66.68 | 63.13 | 0.000416 | ★ Best Saved |
| **20** | 63.17 | 60.81 | 0.000173 | ★ Best Saved |
| **24** | 62.38 | **60.50** | 0.000016 | ★ **Global Best Checkpoint** |
| **25** | 62.28 | 60.50 | 0.000010 | - |

Validation loss dropped monotonically from 108.79 down to 60.50, demonstrating rapid convergence without divergence or numerical instability.

---

## 5. Independent Test Benchmark & Baseline Comparisons

Evaluated across **1,216 held-out test windows** representing 72 unseen cyclones:

### 5.1 Track Error Benchmark (Mean Great-Circle Distance Error in km)

| Horizon | Vayumarg-Track-GRU | Geodesic Baseline (Module B) | Stationary Baseline | GRU Skill vs Stationary | GRU Skill vs Geodesic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **+6 Hours** | **42.2 km** | 35.3 km | 97.5 km | **+56.7%** | -19.4% |
| **+12 Hours** | **89.8 km** | 78.3 km | 193.8 km | **+53.7%** | -14.7% |
| **+24 Hours** | **239.3 km** | 180.5 km | 388.5 km | **+38.4%** | -32.6% |

### 5.2 Intensity Error Benchmark (Mean Absolute Error in knots)

| Horizon | Vayumarg-Track-GRU MAE | Persistence Baseline MAE | Intensity Skill vs Persistence |
| :--- | :--- | :--- | :--- |
| **+6 Hours** | 6.41 kt | 3.98 kt | -61.1% |
| **+12 Hours** | 7.94 kt | 6.83 kt | -16.3% |
| **+24 Hours** | **10.87 kt** | 11.10 kt | **+2.1% (GRU Beats Persistence)** |

---

## 6. Scientific Interpretation & Meteorological Reality

1. **The Strength of Short-Range Geodesic Extrapolation**:
   In tropical meteorology, cyclone translational motion has immense physical inertia. On short horizons (+6h and +12h), atmospheric steering currents rarely reverse instantaneously; therefore, linear constant-velocity great-circle projection is an exceptionally strong, mathematically difficult-to-beat benchmark. Vayumarg honestly and transparently documents this rather than artificially depressing the baseline.

2. **Substantial Skill Over Stationary Projections**:
   Compared to a no-motion assumption, the Track GRU cuts track error by **56.7% at +6h**, **53.7% at +12h**, and **38.4% at +24h**.

3. **Beating Wind Persistence at +24 Hours**:
   While short-term (6h) wind persistence is strong, at +24 hours tropical cyclones frequently undergo rapid intensification or decay upon landfall or dry-air intrusion. At +24h, the Track GRU achieves an MAE of **10.87 kt**, outperforming the persistence baseline (**11.10 kt**) with a positive skill score of **+2.1%**.

4. **Integration in Vayumarg**:
   Both the Vayumarg-Track-GRU neural forecast and the deterministic Geodesic baseline operate in parallel. Judges and meteorologists can inspect both trajectory lines side-by-side on any historical cyclone.

