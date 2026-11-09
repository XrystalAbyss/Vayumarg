# VAYUMARG 3.0 — P1.1 MODEL INPUT CONTRACT & OBSERVATION WINDOW AUDIT

**Audit Date:** 2026-11-07  
**Auditor:** Machine Learning Research Engineer & Scientific Systems Architect  
**Classification:** Model Tensor Specification & Preprocessing Verification  
**Status:** COMPLETE & INDEPENDENTLY RECONCILED  

---

## 1. Sequence Window Semantics & The "24-Hour" Discrepancy

In the Milestone P1-GIT.1 manifest (`checkpoint_cloud_registry_v2.json`), the Track GRU input was described as:
> *"8-step historical trajectory sequence (24h observation window at 3h cadence)"*

### Mathematical Inconsistency & Ground Truth
In regular temporal series:
$$N\text{ samples at cadence }\Delta t \implies (N - 1)\text{ elapsed intervals}$$
For $N = 8$ fixes at $\Delta t = 3.0\text{ hours}$:
$$\text{Elapsed Span} = (8 - 1) \times 3.0 = 21.0\text{ hours}$$

### Source Code Analysis (`src/vayumarg/ml/track/dataset.py` lines 177–204)
* The extraction algorithm slices `window_fixes[:in_steps]` where `in_steps = 8`.
* Fix $k = 0$ is at relative elapsed time $0.0\text{ h}$.
* Fix $k = 7$ (the origin fix from which predictions are launched) is at relative elapsed time $21.0\text{ h}$.
* **Root Cause of "24h":** The "24-hour observation window" was a nominal reporting convention, conflating the count of 3-hour synoptic buckets ($8 \times 3\text{h} = 24\text{h}$) with the physical elapsed interval from the first observation to the current observation.
* **Resolution:** Formally codified in `reports/v3/checkpoint_cloud_registry_v3.json` as:
  * `consecutive_fixes_count`: 8
  * `cadence_hours`: 3.0
  * `elapsed_observation_span_hours`: 21.0
  * `nominal_reporting_cycle_hours`: 24.0

---

## 2. Comprehensive Model Input Specifications

### 2.1 Satellite CNN (`models/vayumarg/vision/satellite_cnn_best.pt`)
* **Input Tensor Shape:** `[batch_size, 1, 128, 128]`
* **Channel:** Single-channel geostationary infrared telemetry (10.3–10.4 µm).
* **Radiometric Scaling:** Native Kelvin converted to normalized float $[0.0, 1.0]$ and standardized via:
  $$x_{\text{norm}} = \frac{x - 0.45}{0.22}$$
* **Forward Output:**
  * Huber Regression Head: Scalar maximum sustained 1-minute wind speed in knots.
  * Auxiliary Classification Head: 6-class intensity category logits.
* **Weights-Only Status:** Native PyTorch 2.6 safe deserialization verified.

### 2.2 Satellite ConvLSTM (`models/vayumarg/vision/satellite_convlstm_best.pt`)
* **Input Tensor Shape:** `[batch_size, 3, 1, 64, 64]`
* **Sequence Length ($T$):** 3 chronological geostationary IR frames.
* **Temporal Interval:** Irregular satellite observation intervals matching satellite acquisition time (not resampled to uniform grid).
* **Spatial Resolution:** $64 \times 64$ pixels per frame (downsampled from $128 \times 128$ for spatio-temporal memory efficiency).
* **Standardization:** Identical to CNN ($\mu = 0.45, \sigma = 0.22$).
* **Forward Output:**
  * Future Frame Decoder: Tensor `[batch_size, 1, 64, 64]` predicting next-frame normalized IR imagery.
  * Future Intensity Head: Scalar predicted wind speed (knots).
* **Weights-Only Status:** Native PyTorch 2.6 safe deserialization verified.

### 2.3 Track GRU (`models/vayumarg/track_gru_best.pt`)
* **Input Tensor Shape:** `[batch_size, 8, 10]`
* **Sequence Length ($T$):** 8 consecutive 3-hourly synoptic fixes ($21.0\text{ h}$ elapsed span).
* **Feature Ordering & Normalization (10 Features):**
  1. `lat / 30.0`: Latitude normalized by $30^\circ\text{N}$.
  2. `(lon - 75.0) / 30.0`: Longitude centered at $75^\circ\text{E}$ and scaled by $30^\circ$.
  3. `dx_prev / 50.0`: Relative eastward step displacement in km normalized by $50\text{ km}$.
  4. `dy_prev / 50.0`: Relative northward step displacement in km normalized by $50\text{ km}$.
  5. `speed_kmh / 50.0`: Translational velocity in km/h normalized by $50\text{ km/h}$.
  6. `sin(bearing)`: Trigonometric sine of azimuth bearing angle.
  7. `cos(bearing)`: Trigonometric cosine of azimuth bearing angle.
  8. `wind_kt / 150.0`: Maximum sustained wind speed normalized by $150\text{ kt}$.
  9. `delta_wind / 10.0`: 3-hour intensity change normalized by $10\text{ kt}$.
  10. `t / 7.0`: Linear temporal progression index ranging from $0.0$ to $1.0$ across the 8 historical fixes.
* **Forward Output:**
  * Multi-horizon displacement offsets: Tensor `[batch_size, 3, 2]` $(\Delta x, \Delta y)$ for horizons $+6\text{h}$, $+12\text{h}$, $+24\text{h}$.
  * Future wind intensity: Tensor `[batch_size, 3]` for $+6\text{h}$, $+12\text{h}$, $+24\text{h}$.
* **Weights-Only Status:** Native PyTorch 2.6 safe deserialization verified.

### 2.4 Hybrid Residual Model (`models/vayumarg/track_hybrid_residual_best.pt`)
* **Input Tensors:**
  * Kinematic Sequence Tensor: `[batch_size, 8, 10]` (Identical feature contract to Track GRU).
  * Geodesic Baseline Tensor: `[batch_size, 3, 2]` representing uncorrected great-circle displacement vectors $(v_x \cdot \Delta t, v_y \cdot \Delta t)$ for $+6\text{h}, +12\text{h}, +24\text{h}$.
* **Forward Output:**
  * Residual Displacements: Tensor `[batch_size, 3, 2]` bounded via `tanh` scaling.
  * Final Predicted Displacements: Geodesic Baseline $+$ Residual Correction.
  * Predicted Wind Intensity: Tensor `[batch_size, 3]`.
* **Weights-Only Status:** Loaded safely with `weights_only=True` using scoped `torch.serialization.safe_globals([np.dtype, np.dtypes.Float64DType, np._core.multiarray.scalar])`. Zero arbitrary unpickling risk.

---

## 3. Physical Invariant & Geodesic Formulation

* **Coordinate Distance Calculation:** Evaluated via the spherical Law of Haversines using Earth radius $R = 6371.0\text{ km}$.
* **Local Tangent Space Conversion:**
  $$\Delta y = (\phi_2 - \phi_1) \times 111.12\text{ km}$$
  $$\Delta x = (\lambda_2 - \lambda_1) \times 111.12 \times \cos(\phi_{\text{origin}})\text{ km}$$
* **Geodesic Forward Projection:** Constant-velocity spherical vector extrapolation using the translational velocity derived over the most recent 3-hour interval:
  $$v_x = \frac{\Delta x}{3.0},\quad v_y = \frac{\Delta y}{3.0}$$

