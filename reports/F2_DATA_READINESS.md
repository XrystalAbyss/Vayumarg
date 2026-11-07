# VAYUMARG — F2 Scientific Data Readiness & Expansion Strategy

**Milestone:** F2 — Satellite Dataset Discovery, Authentic Imagery Pilot and Spatiotemporal Alignment  
**Execution Date:** 2026-11-01  
**Author:** Principal Scientific Software Architect & ML Dataset Architect  
**Status:** **Verified & Complete**  

---

## 1. Executive Summary

This report evaluates the scientific readiness of Vayumarg's shared data foundation for training and evaluating **Module A** (Satellite Current-State Classification & Intensity Estimation) and **Module B** (Independent Trajectory & Future Wind Forecasting).

It establishes the storage budgets, data expansion pathways, and architectural independence guarantees required before initiating large-scale data acquisition and model development.

---

## 2. Module A Data Readiness: Satellite-Image-to-Intensity Regression

### 2.1 Multi-Spectral Input Formulation
- **Primary Input Channels:** Deep infrared window (`IR1` / `TIR-1` at 10.8 $\mu$m) and upper-tropospheric water vapor (`WV` at 6.8 $\mu$m).
- **Dual-Channel Input Tensor:** $\mathbf{X} \in \mathbb{R}^{201 \times 201 \times 2}$
- **Diurnal Independence:** IR1 and WV operate continuously 24 hours a day with 0.0% missingness under clear/cloudy atmospheric scenes. The visible (`VIS`) channel is rejected as a mandatory input due to 50% diurnal missingness (nighttime solar absence).

### 2.2 Dual Ground-Truth Target Strategy
Models trained on Vayumarg will predict two scientifically segregated intensity targets:
1. **$y_{\text{IMD}}$:** Maximum 3-minute sustained surface wind speed (knots) and discrete IMD stage (`D`, `DD`, `CS`, `SCS`, `VSCS`, `ESCS`, `SuCS`).
2. **$y_{\text{JTWC}}$:** Maximum 1-minute sustained surface wind speed (knots).
- **Independence Guarantee:** Models will optimize a multi-task loss or train separate heads, preventing the conflation of 1-minute and 3-minute meteorological definitions.

---

## 3. Module B Data Readiness: Trajectory & Intensity Forecasting

### 3.1 Strict Architectural Independence
> [!IMPORTANT]
> **Zero Architectural Coupling:**  
> Module B does not depend on Module A predictions. It consumes strictly historical best-track trajectory sequence vectors ($t \le t_0$) and external meteorological reanalysis (e.g. steering flow, deep-layer shear, sea surface temperature). Module B remains fully operational even during satellite communication outages or night passes.

### 3.2 Causal Chronological Sequence Framing
- Input sequence: Historical 24-hour synoptic steps at 3-hour or 6-hour intervals:
  $$\mathbf{S}_t = \left[ (\text{Lat}_k, \text{Lon}_k, V_k, P_k, \Delta \text{Lat}_k, \Delta \text{Lon}_k) \right]_{k=t-24\text{h}}^{t}$$
- Output target: Multi-horizon forecast displacements and wind intensity changes:
  $$\hat{\mathbf{Y}} = \left[ (\Delta \text{Lat}_{t+h}, \Delta \text{Lon}_{t+h}, V_{t+h}) \right]_{h \in \{6, 12, 24, 48, 72\}}$$
- **Leakage Prevention:** Retrospective best-track smoothing is explicitly flagged (`is_retrospective_best_track = True`) so models are validated with realistic operational observation noise.

---

## 4. Controlled Dataset Expansion Strategy (F2.1 Plan)

### 4.1 Storage & Bandwidth Budgeting

| Asset Group | Target Dataset | Expected Count | Unit Size | Total Estimated Storage | Network Impact | Access Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TCIR IO Subset** | Indian Ocean Frames | 3,205 frames | ~380 KB / crop | **~1.2 GB** | Extracted from 9.23 GB archive | Bounded extraction of IO storms |
| **INSAT-3DS Pilot** | L1B Full Disk Granules | 10 granules (DANA 2024) | ~85 MB / granule | **~850 MB** | Direct MOSDAC download | Authenticated session with user credentials |
| **INSAT-3D Pilot** | L1B Historical Granules | 10 granules (AMPHAN 2020) | ~80 MB / granule | **~800 MB** | Direct MOSDAC download | Authenticated session with user credentials |
| **Processed Crops** | Normalized Dual-Channel | 3,500 patches | ~160 KB / patch | **~560 MB** | Local disk processing | Stored in `data/processed/crops/` |
| **Total F2.1 Budget** | Multi-Source Combined | — | — | **~3.41 GB** | Modest, manageable bandwidth | Well within available 170 GB disk space |

### 4.2 Stepwise Rollout Protocol
1. **Step 1 (Selective IO Frame Extraction):** Download `TCIR-CPAC_IO_SH.h5` during an approved maintenance window, stream-extract the 3,205 Indian Ocean frames into `data/interim/tcir_io/`, and delete the remaining unneeded non-IO frames to conserve disk storage.
2. **Step 2 (MOSDAC Bounded Pilot):** User configures their personal MOSDAC credentials into `.env.local`; pipeline downloads 2–3 full-disk granules for Cyclone DANA (October 2024) and verifies physical brightness temperature calibration.
3. **Step 3 (Cropping & Association):** Automated cyclone eye cropping centers patches around the best-track eye fix, registering crops in `satellite_processed_crops` and associations in `satellite_track_associations`.

