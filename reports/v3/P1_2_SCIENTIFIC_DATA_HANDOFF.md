# VAYUMARG 3.0 — P1.2 SCIENTIFIC DATA HANDOFF INVENTORY & ROADMAP

**Document ID:** `reports/v3/P1_2_SCIENTIFIC_DATA_HANDOFF.md`  
**Milestone:** Transition from P1.1 (Backend Stabilization & Release Freeze) to P1.2 (Authentic INSAT Scientific Data Development)  
**Lead Roles:** Scientific Software Maintainer, Remote Sensing QA Lead, Application Security Reviewer  
**Date:** 2026-11-09  
**Status:** **AUTHORITATIVE PLANNING HANDOFF (ZERO RETRAINING / ZERO INGESTION DURING FREEZE)**  

---

## 1. Executive Context & Scope Boundary

With the completion and verification of the Vayumarg P1.1 backend stabilization milestone, the system architecture, REST contracts, database persistence, and security controls are formally frozen. Milestone P1.2 focuses strictly on authentic INSAT meteorological data science, multi-spectral radiometric calibration, and bounded temporal processing.

> [!IMPORTANT]
> **Strict Phase Boundary Policy:**
> - No new datasets are downloaded or ingested during the P1.1 release freeze.
> - No model architectures or production weights are altered.
> - The four existing trained checkpoints remain the immutable baseline for all subsequent comparisons.

---

## 2. Source Granule Inventory: FANI (2019) & TAUKTAE (2021)

Two authentic, full-disk Level 1B INSAT-3DR granules are present in local offline storage, acquired from the ISRO MOSDAC data archive under research credentials:

| Granule File Identifier | Satellite Sensor | Target Cyclone Event | Observation Timestamp (UTC) | File Size | Data Status & Ingestion Integrity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `3RIMG_02MAY2019_0600_L1B_STD_V01R00.h5` | **INSAT-3DR** | **Cyclone FANI** (BoB, ESCS / SuCS intensity) | `2019-05-02 06:00:00` | ~300.2 MB | Raw Full-Disk Level 1B HDF5; uncropped, uncorrupted, verified checksums. |
| `3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5` | **INSAT-3DR** | **Cyclone TAUKTAE** (Arabian Sea, Extreme ESCS) | `2021-05-16 23:58:00` | 301,621,093 B | Raw Full-Disk Level 1B HDF5; uncropped, uncorrupted, verified checksums. |

### Canonical Best-Track Synchronization:
- **Cyclone FANI (`2019116N02090`):** Fix coordinates for `2019-05-02 06:00 UTC`: Lat $16.0^\circ\text{N}$, Lon $84.5^\circ\text{E}$, Max Sustained Wind $115\text{ kt}$ (IMD Category: Extremely Severe Cyclonic Storm).
- **Cyclone TAUKTAE (`2021133N10071`):** Fix coordinates for `2021-05-16 23:58 UTC`: Lat $18.5^\circ\text{N}$, Lon $71.6^\circ\text{E}$, Max Sustained Wind $100\text{ kt}$ (IMD Category: Extremely Severe Cyclonic Storm).

---

## 3. Available Complete Multi-Channel HDF5 Crops

Four standardized $201 \times 201$ multi-spectral HDF5 crops were processed, radiometrically calibrated, and verified during F2.4 acceptance. They reside in `data/satellite/crops/`:

1. **Super Cyclonic Storm AMPHAN (2020):** `AMPHAN_20200518_1200_TIR1.h5`
   - Eye Center: $13.2^\circ\text{N}, 86.3^\circ\text{E}$
   - Resolution: $201 \times 201$ nodes (4.0 km/px, $800 \times 800\text{ km}$ synoptic bounding box)
   - Channels: TIR-1 ($10.8\ \mu\text{m}$), TIR-2 ($12.0\ \mu\text{m}$), MIR ($3.9\ \mu\text{m}$), WV ($6.9\ \mu\text{m}$)
2. **Extremely Severe Cyclonic Storm BIPARJOY (2023):** `BIPARJOY_20230611_0600_TIR1.h5`
   - Eye Center: $18.6^\circ\text{N}, 67.8^\circ\text{E}$
   - Resolution: $201 \times 201$ nodes across 4 calibrated bands.
3. **Severe Cyclonic Storm REMAL (2024):** `REMAL_20240525_1800_TIR1.h5`
   - Eye Center: $19.1^\circ\text{N}, 89.6^\circ\text{E}$
   - Resolution: $201 \times 201$ nodes across 4 calibrated bands.
4. **Cyclonic Storm DANA (2024):** `DANA_20241024_1800_TIR1.h5`
   - Eye Center: $20.4^\circ\text{N}, 87.2^\circ\text{E}$
   - Resolution: $201 \times 201$ nodes across 4 calibrated bands.
   - **Operational Governance Check:** Bounded prior to overland dissipation; post-landfall tracking restricted per IMD operational protocol.

---

## 4. Cadence & Observation Gaps

Forensic audit of historical satellite acquisitions identifies key observational limitations:
- **Temporal Cadence Inconsistency:** INSAT-3D/3DR operational scans alternate between half-hourly and hourly modes, occasionally interrupted by rapid-scan protocols (10-minute sector scans) or calibration outages.
- **Missing Intermittent Timestamps:** 
  - FANI: Rapid intensification phase between `2019-04-30 18:00 UTC` and `2019-05-01 06:00 UTC` lacks continuous 30-minute full-disk coverage in local offline archives.
  - TAUKTAE: Peak intensity frame at `2021-05-17 12:00 UTC` is currently unacquired (only `16MAY2021_2358` is present locally).
- **Water Vapor Resolution Mismatch:** INSAT-3D Water Vapor (WV) channels have an 8.0 km nominal sub-satellite resolution compared to 4.0 km for TIR-1/TIR-2, requiring bilinear interpolation to coregister to the $201 \times 201$ grid.

---

## 5. Existing Calibration & Preprocessing Pipeline

The calibration codebase in [`src/vayumarg/satellite/calibration.py`](file:///c:/Users/astra/Desktop/Project/Vayumarg/src/vayumarg/satellite/calibration.py) and [`src/vayumarg/satellite/crop_engine.py`](file:///c:/Users/astra/Desktop/Project/Vayumarg/src/vayumarg/satellite/crop_engine.py) implements standardized radiometric conversion:

1. **Digital Count to Radiance ($L_\lambda$):**
   $$L_\lambda = \text{Slope} \times \text{Count} + \text{Intercept}$$
2. **Radiance to Effective Brightness Temperature ($T_b$ via Planck Inversion):**
   $$T_b = \frac{c_2 \cdot \nu}{\ln\left(1 + \frac{c_1 \cdot \nu^3}{L_\lambda}\right)}$$
   followed by sensor-specific central wavenumber correction:
   $$T = \frac{T_b - \beta}{\alpha}$$
3. **Physical Domain Clamping:**
   - Thermal IR (TIR-1, TIR-2): Clamped strictly to $[170.0\text{ K}, 340.0\text{ K}]$.
   - Water Vapor (WV): Clamped strictly to $[190.0\text{ K}, 280.0\text{ K}]$.
   - Mid-Infrared (MIR): Day/night saturation filtering applied.

---

## 6. Known Data Governance & Legal Restrictions

- **ISRO MOSDAC Level 1B Governance:** Authentic INSAT satellite telemetry is provided for non-commercial academic research. While derivative scientific metrics, model loss curves, and processed bounding vectors are open, raw HDF5 arrays and rendered high-resolution scenes must **never** be checked into public Git repositories without explicit data-sharing agreements.
- **Repository Cleanliness Policy:** All `.h5`, `.hdf5`, `.nc`, and rendered satellite PNGs are permanently excluded via `.gitignore` and screened via automated pre-commit scanners.

---

## 7. Immutable Baseline Machine Learning Models

The following 4 production checkpoints in `models/vayumarg/` are permanently frozen:

| Model Architecture | Task | Canonical Input Specification | Target Output & Invariants | Checkpoint SHA-256 |
| :--- | :--- | :--- | :--- | :--- |
| **ResNet-18 (`cnn_intensity`)** | Cyclone Intensity Estimation | `[1, 1, 128, 128]` normalized thermal IR ($\mu=0.45, \sigma=0.22$) | Wind in knots (scalar) + 6 category logits | `678fa428...` |
| **ConvLSTM (`convlstm`)** | Spatiotemporal Extrapolation | `[1, 3, 1, 64, 64]` (sequence length $T=3$) | Next frame `[1, 1, 64, 64]` + future wind | `8ef621db...` |
| **Trajectory GRU (`gru_trajectory`)** | Track Prediction | `[1, 8, 10]` (8 history fixes, 10 kinematic features) | Displacement `[1, 3, 2]` (+6h, +12h, +24h) | `26b3a3ea...` |
| **Physics-Informed Hybrid (`hybrid_physics`)** | Physics Residual Extrapolation | `[1, 8, 10]` features + `[1, 3, 2]` geodesic baseline displacement | Final displacement `[1, 3, 2]` + bounded physics residuals | `ecdf4567...` |

> [!WARNING]
> These architectures and checkpoints serve as the scientific benchmark controls. P1.2 activities must compare against these numbers without overwriting the checkpoints.

---

## 8. Recommended Bounded Temporal-Processing Pilot for P1.2

To expand scientific dataset coverage in Milestone P1.2 without introducing scope bloat or infrastructure regression:

1. **Step 1: Automated Local Crop Generation for FANI & TAUKTAE**
   - Execute `crop_engine.py` on the two uncropped granules already on disk (`3RIMG_02MAY2019_0600` and `3RIMG_16MAY2021_2358`).
   - Validate $201 \times 201$ 4-channel matrix generation with zero NaN/Inf values.
   - Register the resulting crops into PostgreSQL `satellite_crops` with foreign key association to existing `storms` records.
2. **Step 2: Temporal Sequence Extraction Pilot**
   - For Cyclone BIPARJOY and Cyclone REMAL (where multiple temporal frames exist in historical MOSDAC catalogs), establish a bounded pilot of 3 consecutive frames spaced 3 hours apart.
   - Verify alignment with the ConvLSTM `[B, 3, 1, 64, 64]` inference contract.
3. **Step 3: Verification & Parity Assertions**
   - Ensure all expanded datasets pass `tests/integration/test_real_hdf5_multichannel.py`.
   - Maintain 100% green test passing on all existing 182 tests.
