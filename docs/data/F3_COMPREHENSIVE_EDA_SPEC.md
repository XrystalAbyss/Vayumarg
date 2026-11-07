# VAYUMARG — F3 Comprehensive Exploratory Data Analysis (EDA) Specification

**Document Version:** 1.0.0-PROPOSED  
**Stage:** Specification for Execution Post-Dataset Harmonization  
**Author:** Principal Scientific Software Architect & ML Dataset Architect  
**Project:** Vayumarg (SIH26070 / CV-IP, Team VortexA)  
**Target Modules:** Module A (Current-State Satellite Intensity Estimation) & Module B (Future Trajectory/Intensity Forecasting)  

---

## Executive Overview

This specification establishes the scientific blueprint, statistical methodologies, visualization standards, and leakage audits for the comprehensive Exploratory Data Analysis (EDA) to be conducted after final multi-source satellite acquisition and prior to machine learning model training.

The final EDA execution will produce:
- Interactive Jupyter Notebooks (`notebooks/eda/`)
- A standalone, publication-grade HTML analysis report (`reports/eda/F3_COMPREHENSIVE_EDA_REPORT.html`)
- Machine-readable statistical metadata cards (`reports/eda/data_profile.json`)
- High-resolution SVG/PNG figure assets (`reports/eda/figures/`)

---

## 1. Source Inventory and Dataset Lineage

### 1.1 Multi-Source Provenance Matrix
Document the end-to-end lineage of all ingested meteorological and remote-sensing assets:
- **Best-Track Data:** NOAA IBTrACS v04r01 North Indian Ocean archive (`ibtracs.NI.list.v04r01.csv`, 27,895,917 bytes, SHA-256 `6e0dd2dde1f22c4bf03995beb21944bf5976536c747b23ba85c6d300aeab69ff`).
- **TCIR Benchmark Imagery:** NTU CSIE multi-channel HDF5 archive (`TCIR-CPAC_IO_SH.h5`, 9.23 GB, 3,205 Indian Ocean frames).
- **MOSDAC ISRO Imager Archives:** INSAT-3DS (`3SIMG_L1B_STD`), INSAT-3DR (`3RIMG_L1B_STD`), and INSAT-3D (`3DIMG_L1B_STD`) Level-1B standard acquisition granules.

### 1.2 Cryptographic Lineage Tracking
- Trace every processed image crop back to:
  $$\text{Crop ID} \longrightarrow \text{Granule ID} \longrightarrow \text{Raw File SHA-256} \longrightarrow \text{Preprocessing Git/Manifest Version}$$
- Verify that every ground-truth label traces to its internal `storm_id`, `source_agency`, and `source_record_id`.

---

## 2. Completeness and Missingness Audits

### 2.1 Tabular Meteorological Fields
- Compute missingness percentage across all 104,374 observations for:
  - Surface wind speed (`wind_speed_knots`)
  - Central surface pressure (`central_pressure_hpa`)
  - Pressure drop (`pressure_drop_hpa`)
  - Radius of maximum winds ($R_{\max}$)
  - Environmental pressure of outermost closed isobar ($P_{\text{oci}}$)
- Confirm strict SQL `NULL` retention (0 instances of zero-coerced missing values).

### 2.2 Satellite Image Pixels
- Analyze spatial missingness patterns per channel:
  - **IR1 (10.8 $\mu$m):** Expected 0.0% missing in valid scenes; detect sensor scanline dropouts.
  - **WV (6.8 $\mu$m):** Evaluate upper-tropospheric saturation and boundary fill values.
  - **VIS (0.65 $\mu$m):** Quantify diurnal missingness (daylight availability vs. 100% nighttime NaN).
  - **PMW (37/85 GHz):** Map orbital swath boundary cutoffs and interpolation artifacts.

---

## 3. Historical Temporal and Seasonal Patterns

### 3.1 Seasonal Bimodality Analysis
The North Indian Ocean exhibits a distinct bimodal cyclone climatology driven by the Southwest Monsoon:
- **Pre-Monsoon Peak:** April – May – June (e.g., AMPHAN May 2020, BIPARJOY June 2023, REMAL May 2024).
- **Monsoon Hiatus:** July – August (characterized by high vertical wind shear suppressing cyclogenesis).
- **Post-Monsoon Primary Peak:** October – November – December (e.g., DANA October 2024, FENGAL November 2024).

### 3.2 Centennial Trend Profiling (1842–2026)
- Quantify storm frequency across 185 seasons.
- Evaluate decadal shifts in Arabian Sea vs. Bay of Bengal genesis frequency.

---

## 4. Geographic Storm-Track Distributions

### 4.1 Basin Density & Heatmaps
- Generate kernel density estimation (KDE) heatmaps for:
  - Cyclogenesis locations ($t = 0$)
  - Peak intensity locations ($t = t_{\text{vmax}}$)
  - Landfall coordinate points ($t = t_{\text{landfall}}$)
- Partition spatial density between Bay of Bengal (BB) and Arabian Sea (AS).

### 4.2 Landfall Distance Correlation
- Analyze storm decay rates as a function of `dist2land` (distance to coastline in km).

---

## 5. Category and Wind-Intensity Distributions

### 5.1 IMD Cyclone Stage Histogram
Profile the frequency distribution of official IMD intensity stages:
- Depression (`D`: 17–27 kts)
- Deep Depression (`DD`: 28–33 kts)
- Cyclonic Storm (`CS`: 34–47 kts)
- Severe Cyclonic Storm (`SCS`: 48–63 kts)
- Very Severe Cyclonic Storm (`VSCS`: 64–89 kts)
- Extremely Severe Cyclonic Storm (`ESCS`: 90–119 kts)
- Super Cyclonic Storm (`SuCS`: $\ge 120$ kts)

### 5.2 Wind Speed Continuous Distribution
- Fit parametric probability distributions (Weibull, Lognormal, Gamma) to maximum sustained winds.
- Calculate skewness, kurtosis, and empirical percentiles (P10, P50, P90, P99).

---

## 6. Agency Duplication and Disagreements

### 6.1 IMD (3-min) vs. JTWC (1-min) Disagreement Metrics
- Compare simultaneously reporting agencies for identical storm timestamps:
  $$\Delta V = V_{\text{JTWC}} - V_{\text{IMD}}$$
- Statistically evaluate the empirical Harper-Kepert-Powell conversion ratio:
  $$\bar{R} = \frac{V_{\text{1-min}}}{V_{\text{3-min}}} \approx 1.08 \text{ to } 1.15$$
- Document coordinate offset distribution between IMD and JTWC eye positions:
  $$\Delta d = \text{Haversine}(\text{Lat}_{\text{IMD}}, \text{Lon}_{\text{IMD}}, \text{Lat}_{\text{JTWC}}, \text{Lon}_{\text{JTWC}})$$

### 6.2 WMO Duplicate Audit
- Enforce strict exclusion of WMO New Delhi entries that duplicate direct IMD records to prevent artificial double-weighting in ML loss functions.

---

## 7. Source-Era and Sensor Biases

### 7.1 Historical Epoch Biases
Document observational uncertainty shifts across the 3 historical eras:
1. **Pre-1900 Era (265 storms):** Maritime ship logs; Beaufort wind estimations; uninstrumented pressures.
2. **1900–1981 Era (1,131 storms):** Coastal synoptic pressure gauges; early radar; intermittent aircraft reconnaissance.
3. **1982–Present Modern Era (464 storms):** Geostationary infrared Dvorak technique; scatterometry; microwave sounding.

### 7.2 Satellite Sensor Calibration Shifts
- Evaluate calibration step-changes between:
  - AVHRR / GridSat-B1
  - INSAT-3D (operational 2013–2024, sub-sat 82°E)
  - INSAT-3DR (operational 2016–present, sub-sat 74°E)
  - INSAT-3DS (operational 2024–present, sub-sat 74°E)

---

## 8. Multi-Spectral IR / WV Imagery Distributions & QC

### 8.1 Physical Value Distributions & Calibration Boundary Validation
- **TIR-1 (10.8 $\mu$m):** Cloud-top brightness temperature histograms. 
  - *Lower Calibration Boundary Audit:* Formally audit the 179.86 K lower boundary. In INSAT-3DR L1B standard calibration LUTs (`IMG_TIR1_TEMP`), all digital counts $\ge 921$ are clamped to the constant floor of $179.85948\text{ K}$. Do not mistake table clamping for unclipped overshooting cloud top measurements.
  - Quantify the frequency of lower-boundary clamped pixels per storm phase.
- **WV (6.8 $\mu$m):** Mid-to-upper tropospheric water vapor brightness temperature distribution ($180\text{ K} - 265\text{ K}$, clamped $\ge 995$ to 179.69 K).
- **Split-Window Difference ($\Delta T_{\text{split}} = T_{\text{TIR1}} - T_{\text{TIR2}}$):** Water vapor attenuation and thin cirrus anvil identification.
- **Convective Mask ($\Delta T = T_{\text{TIR1}} - T_{\text{WV}}$):** Deep convective cloud masking ($T_{\text{TIR1}} - T_{\text{WV}} \le 0\text{ K}$).

### 8.2 Native vs. Resampled Effective Resolution Governance
- **Resolution Accounting:** Explicitly maintain separation between:
  - *Native Sensor Resolutions:* VIS (1.0 km), SWIR (1.0 km), TIR-1 (4.0 km), TIR-2 (4.0 km), MIR (4.0 km), WV (8.0 km).
  - *Target Common Crop Grid:* Uniform 4.0 km spatial grid ($201 \times 201$ pixels across 800.0 km extent).
- **No Pseudo-Resolution Claim:** When WV (native 8.0 km) is resampled via bilinear interpolation to match the 4.0 km TIR-1 grid, record `effective_resolution_km = 8.0`. The EDA report must explicitly state that resampling provides tensor co-registration for CNN backbones but contains no new high-frequency physical information.

### 8.3 Image Quality Control & Space-Fill Masks
- **Space-Fill Masking:** In raw 10-bit count arrays, digital count `1023` represents space background (`_FillValue: 1023`). Quantify disk-boundary clipping and ensure all pixels outside the Earth's limb are strictly masked before computing spatial statistics.
- **Detector Line Striping & Scan Artifacts:** Audit detector scanline dropouts and limb-cooling effects.

---

## 9. Satellite/Track Alignment and Matching Quality

### 9.1 Temporal Matching and Scan-Line Timing Uncertainty
- Plot histogram of $|\Delta t| = |t_{\text{satellite}} - t_{\text{best\_track}}|$ for all paired crops.
- **Scan-Line Progression vs. Scene Timestamp:** INSAT full-disk frames take $\approx 4.3\text{ minutes}$ to acquire (`Acquisition_Start_Time` to `Acquisition_End_Time`). For cyclone centers located at specific row indices (e.g., row 835 of 2816), evaluate actual scanline passage time rather than relying solely on product header start/end timestamps.
- Benchmark sensitivity of intensity regression to matching windows:
  $$\tau \in \{15\text{ min}, 30\text{ min}, 45\text{ min}, 60\text{ min}\}$$

### 9.2 Vortex Centering Error & Agency Disagreements
- Separate **grid quantization residual** ($\approx 1.0\text{ km}$ due to 4 km pixel resolution) from **inter-agency storm-center disagreement** (e.g. 91.1 km between IMD post-season reanalysis and JTWC operational fix for REMAL).
- Do not represent geometric heuristic matching scores as calibrated Bayesian confidence probabilities.

---

## 10. Temporal Sequence Coverage (Module B)

### 10.1 Trajectory Length Distribution
- Distribution of synoptic steps per cyclone ($N_{\text{steps}}$).
- Minimum track length threshold for sequence modeling ($N \ge 8$ steps / 24 hours).

### 10.2 Synoptic Sampling Regularity
- Audit time-interval delta ($\Delta t_{\text{step}} = t_{k} - t_{k-1}$).
- Standardize interpolation policy for irregular non-synoptic intermediate fixes.

---

## 11. Class Imbalance and Rare Extremes

### 11.1 Severe Cyclone Scarcity
- Quantify class imbalance: Super Cyclones (`SuCS`) comprise only 25 track points (0.26% of IMD records).
- Propose mitigation strategies: Focal loss, cost-sensitive re-weighting, and stratified synthetic oversampling.

### 11.2 Rapid Intensification (RI) Events
- Define RI in North Indian Ocean: $\ge 30\text{ kts}$ increase in 24 hours (or $\ge 15\text{ kts}$ in 12 hours).
- Identify and profile canonical RI cases (e.g., AMPHAN May 2020: 30 kts $\to$ 130 kts in 36 hours).

---

## 12. Cross-Basin and Historical Anomalies

### 12.1 Trans-Oceanic Systems
- Document 91 storms with 7,707 points outside the 0–40°N, 30–105°E box.
- Enforce strict exclusion of high-latitude Arctic transitions (e.g. Hurricane Faith 83°N) from regional NIO training splits.

---

## 13. Storm-Safe Train / Validation / Test Planning

### 13.1 Strict Storm-Level Partitioning
> [!CAUTION]
> **Data Leakage Prohibition:**  
> Never split by random image frame! Consecutive 15-minute or 3-hour frames from the same storm are strongly autocorrelated. Splitting frames randomly inflates validation accuracy spuriously.

- Split policy: Partition **by unique storm identity** (`storm_id` / `sid`).
- Proposed split ratio:
  - **Training Set:** 70% of storms (~325 satellite-era storms)
  - **Validation Set:** 15% of storms (~70 satellite-era storms)
  - **Test Set:** 15% of storms (~70 satellite-era storms, including canonical benchmarks AMPHAN, BIPARJOY, REMAL, DANA)

### 13.3 Train-Only Normalization & Contamination Prevention
- All feature scaling parameters (e.g. channel mean $\mu_{\text{train}}$ and standard deviation $\sigma_{\text{train}}$ for brightness temperature, or min/max for coordinates) must be computed **strictly on the training split**.
- Never compute global normalization across the entire dataset prior to splitting.
- Explicitly log normalization scalars per split in `data_profile.json`.

---

## 14. Temporal Leakage and Duplicate-Image Audits

- **Sample Deduplication (Frames vs. Associations):** Audit unique source granules $\to$ unique image frames $\to$ unique crops $\to$ multiple agency label associations. Ensure that multiple agency estimates for the same frame are segregated so that 1 image crop equals 1 atomic training sample with multi-label fields, eliminating spurious duplicate-sample loss weighting.
- Verify zero forward-in-time leakage in Module B:
  $$\text{Features}(t) \subset \{X_\tau \mid \tau \le t_0\}$$
- Compute pairwise perceptual / SSIM hash distances between adjacent frames to remove static duplicate acquisitions.

---

## 15. Model-Ready Record Retention Funnel

Profile the exact attrition / retention funnel across all processing stages:
1. **Raw Ingested Best-Track Fixes:** 104,374 total historical observations.
2. **Satellite Era Filtering (1982–Present):** Modern instrumented era subset.
3. **Satellite Image Availability:** Subset with authentic co-located INSAT / TCIR frames.
4. **Quality & Space-Fill Pass:** Frames with $< 5\%$ space-fill and zero severe detector corruption.
5. **Multi-Agency Ground Truth Availability:** Non-null IMD (3-min) or JTWC (1-min) wind speeds.
6. **Temporal Alignment Window ($\le 30\text{ min}$):** Tight synoptic synchronization.
7. **Spatial Proximity Threshold ($\le 50\text{ km}$):** Valid vortex coverage.
8. **Final MODEL_ELIGIBLE Dataset:** Canonical training/validation/test tensors.

---

## 16. Recommended Baseline Model Complexity

### Module A (Intensity Estimation)
- Baseline 1: Classical statistical Dvorak proxy (minimum central IR brightness temperature).
- Baseline 2: ResNet-18 / EfficientNet-B0 taking dual-channel (IR1 + WV) $201 \times 201$ input patches.
- Loss Function: Huber Loss or Root Mean Squared Error (RMSE) against IMD 3-min sustained wind.

### Module B (Trajectory & Intensity Forecasting)
- Baseline 1: CLIPER (Climatology and Persistence) statistical benchmark.
- Baseline 2: Bidirectional LSTM / GRU consuming past 24-hour synoptic sequence vectors $[x, y, v, p, \Delta x, \Delta y]$.
- Evaluation Metrics: Along-track error (ATE), cross-track error (CTE), and mean absolute error (MAE) in knots.

---

## 17. Known Dataset Limitations and Scientific Caveats

1. **Non-Uniform Averaging Periods:** Ground truth winds must never be pooled without agency stratification.
2. **Nighttime Visible Channel Invalidation:** VIS channel is unavailable for 50% of diurnal cycles.
3. **Post-Season Best-Track Smoothing:** IBTrACS positions represent smoothed post-event reanalyses, whereas operational forecast models operate on noisy real-time advisory fixes.
4. **Resolution Discrepancies:** INSAT-3D/3DR/3DS have differing nadir resolutions across channels (1 km VIS vs 4 km IR vs 8 km WV).

