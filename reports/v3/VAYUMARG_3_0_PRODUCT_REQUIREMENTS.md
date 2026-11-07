# VAYUMARG 3.0 — PRODUCT REQUIREMENTS DOCUMENT (PRD)

**Document Version:** 3.0.0-PROPOSAL  
**Date:** 7 November 2026  
**Status:** DRAFT SPECIFICATION FOR PHASE P1  
**Target Delivery:** Q1 2027  
**System Title:** VAYUMARG — Tropical Cyclone Intelligence & Scientific Decision-Support Platform  

---

## 1. Vision & Core Philosophy

Vayumarg 3.0 is designed as a rigorous, evidence-driven meteorological intelligence platform specifically tailored for the **North Indian Ocean basin (Bay of Bengal and Arabian Sea)**.

The transition from the hackathon prototype (v2.2.3) to Vayumarg 3.0 establishes five foundational principles:
1. **Physical Grounding over AI Hype:** Machine learning models must complement, explain, or improve upon physical and kinematic baselines. Where physics beats neural networks (as in geodesic track extrapolation), physics remains primary.
2. **Absolute Data Provenance:** Every satellite pixel, track fix, and intensity label must trace back to immutable, cryptographically verifiable source data (ISRO MOSDAC, NOAA IBTrACS, IMD RSMC).
3. **No Synthetic Fiction:** The system shall never fabricate mock meteorological data or obscure data gaps. Missing observations must remain explicit `NULL` values.
4. **Meteorological Standards Compliance:** Operational 3-minute sustained winds (IMD standard) and 1-minute sustained winds (JTWC standard) must be rigorously separated.
5. **Operational Resilience:** The platform must execute in both connected enterprise environments (Docker PostGIS + GPU acceleration) and disconnected field operations (local SQLite/JSON cache + CPU fallback).

---

## 2. Target User Personas

| Persona | Role | Primary Objective in Vayumarg | Critical Requirements |
| :--- | :--- | :--- | :--- |
| **Operational Cyclone Forecaster** | RSMC New Delhi / IMD Duty Officer | Monitor active systems, evaluate multi-horizon trajectories (+6h, +12h, +24h), assess rapid intensification risk. | High reliability, low latency, clear uncertainty cones, adherence to official IMD 3-min averaging. |
| **Remote Sensing Researcher** | ISRO SAC / Academic Scientist | Analyze multispectral INSAT brightness temperatures, calibrate Dvorak BD enhancements, evaluate cold cloud tops. | Access to uncalibrated and calibrated physical Kelvin arrays, radial profiles, azimuthal symmetry. |
| **Machine Learning Engineer** | Deep Learning Research Lead | Train, evaluate, and benchmark vision and trajectory architectures under strict storm-disjoint splits. | Forensic release gates, reproducible manifests, latency benchmarks, prevention of data leakage. |
| **Emergency Management Director** | NDRF / State Disaster Management | Understand landfall timing, coastal impact zones, and historical analog storm behaviors. | Clear visual basemaps, intuitive summaries, non-misleading confidence bounds. |

---

## 3. Functional Requirements

### 3.1 Module A: Authentic Satellite Vision & Radiometric Analytics
- **FR-A01 (Level-1B Ingestion):** Automated ingestion of ISRO MOSDAC INSAT-3DR and INSAT-3DS Imager Level-1B HDF5 containers.
- **FR-A02 (Radiometric Calibration):** Conversion of raw sensor counts into physical Brightness Temperature ($T_B$) in Kelvin using official instrument Look-Up Tables.
- **FR-A03 (Spatial Coregistration):** Automatic extraction of $201 \times 201$ pixel grids ($804 \times 804\text{ km}$) centered on the cyclone vortex for TIR-1, TIR-2, WV, and MIR channels.
- **FR-A04 (Physical Analytics):**
  - Cold cloud canopy area quantification below $200\text{ K}$, $220\text{ K}$, and $240\text{ K}$ in square kilometers.
  - Radial brightness temperature profile from storm eye to $400\text{ km}$ radius in $20\text{ km}$ concentric rings.
  - Azimuthal convective symmetry index ($\sigma_T / \mu_T$).
  - Detection and reporting of sensor LUT floor clamping ($179.86\text{ K}$).
- **FR-A05 (Scientific Colormaps):** Real-time rendering of Dvorak Enhanced BD curve, Inverted Thermal Grayscale, and Thermal Rainbow palettes with calibrated measurement legends.

### 3.2 Module B: Trajectory & Intensity Decision Support
- **FR-B01 (Deterministic Geodesic Engine):** High-precision constant-velocity geodesic extrapolation over the WGS84 ellipsoid for +6h, +12h, and +24h forecast horizons.
- **FR-B02 (Ground-Truth Leakage Protection):** Strict issue-time constraint enforcement ($t_{\text{obs}} \le t_{\text{issue}}$) preventing retrospective look-ahead corruption.
- **FR-B03 (Hindsight Error Verification):** Real-time comparison of forecasts against subsequent historical observations, calculating Great-Circle error in kilometers, cross-track error, and along-track error.
- **FR-B04 (Atmosphere-Aware Hybrid Modeling):** Research baseline combining geodesic translation with deep vertical wind shear and steering flow vectors from atmospheric reanalysis.
- **FR-B05 (Calibrated Cone of Uncertainty):** Dynamic 67% and 90% empirical error cones derived from historical North Indian Ocean forecast error distributions.

### 3.3 Module C: AI Model Lab & Governance
- **FR-C01 (Forensic Release Gates):** Checkpoint SHA-256 verification prior to model memory allocation. Quarantining of any modified or unauthenticated weights.
- **FR-C02 (Single-Frame Intensity Regression):** ResNet-18 single-channel infrared intensity prediction with dual regression and classification heads.
- **FR-C03 (Spatiotemporal Sequence Kinematics):** ConvLSTM next-frame cloud advection prediction with dynamic elapsed sequence time reporting.
- **FR-C04 (Domain Transfer Disclaimers):** Mandatory disclosure panels highlighting spectral shifts ($\Delta \lambda = 0.5\text{ µm}$ between GOES and INSAT) and averaging period distinctions.

---

## 4. Non-Functional Requirements

| Metric / Dimension | Target Specification | Verification Method |
| :--- | :--- | :--- |
| **Inference Latency (GPU)** | $\le 20\text{ ms}$ per image on NVIDIA RTX 4050. | Automated benchmark script (`torch.cuda.Event`). |
| **Inference Latency (CPU)** | $\le 250\text{ ms}$ per image on modern x86-64 CPU. | Automated CPU fallback test. |
| **API Response Time** | $\le 100\text{ ms}$ for 95th percentile REST queries. | Uvicorn benchmark suite. |
| **Offline Reliability** | 100% functionality for cached demonstration cyclones. | Integration test with PostgreSQL stopped. |
| **Test Coverage** | $\ge 85\%$ line coverage across `src/vayumarg/`. | Pytest coverage reporter (`pytest --cov`). |
| **UI Bundle Size** | $\le 800\text{ KB}$ gzipped production assets. | Vite build analyzer. |

