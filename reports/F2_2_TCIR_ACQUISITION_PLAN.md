# Vayumarg — Milestone F2.2 Real TCIR Integration & Acquisition Plan

**Date:** 01 November 2026  
**Status:** ARCHITECTURE DESIGN & F2.3 ROADMAP  
**Author:** Principal Remote-Sensing Engineer & Meteorological Data Scientist  
**Milestone:** F2.2 (Multi-Channel INSAT Validation)

---

## 1. Context & Motivation

In milestone F2, a 12-sample synthetic pilot demonstrated TCIR-format adapter logic. In milestone F2.1, a rigorous provenance audit uncovered that the pilot used synthetically generated tensors rather than authentic satellite observations. Milestone F2.2 now defines the official scientific blueprint for acquiring, validating, and integrating authentic TCIR (Tropical Cyclone Image and Best-Track Dataset) data in future milestone F2.3.

---

## 2. Authentic TCIR Dataset Profile

- **Source Reference:** Chen, B.-F., Chen, B., Lin, K.-T., & Lin, C.-C. (2020). *TCIR: A Tropical Cyclone Image and Best-Track Dataset for Intensity Estimation and Forecasting*. IEEE Transactions on Geoscience and Remote Sensing, 58(7), 5174–5188.
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Official Repository:** National Taiwan University (NTU) CSIE / Kaggle Open Dataset (`tcir-dataset`).
- **Archive File Structure:**
  - `TCIR-IO.h5` (~14.2 GB): Indian Ocean subset (includes both North Indian Ocean and South Indian Ocean cyclones from 2003 to 2017).
  - Channels: Infrared (IR), Water Vapour (WV), Visible (VIS), and Passive Microwave (PMW).
  - Spatial Resolution: $201 \times 201$ pixels per storm patch at $4.0\text{ km}$ spacing.

---

## 3. Scientific Differences & Alignment Requirements

Integrating authentic TCIR data into Vayumarg's North Indian Ocean foundation requires resolving three critical scientific differences:

### 3.1 Wind Averaging Interval & Agency Bias
- **TCIR Best-Track Labels:** Sourced exclusively from JTWC advisories, recording **1-minute maximum sustained winds**.
- **Vayumarg Primary Labels:** Sourced from IMD (RSMC New Delhi), recording **3-minute maximum sustained winds**.
- **Action Plan:** TCIR observations must be mapped to Vayumarg's secondary agency schema (`secondary_jtwc`). Under no circumstances will TCIR 1-minute winds overwrite IMD 3-minute ground truth without explicit conversion flags.

### 3.2 Basin Hemispheric Rotation & Coriolis Effect
- `TCIR-IO.h5` combines North Indian Ocean (`NI`) and South Indian Ocean (`SI`) cyclones.
- Tropical cyclones in the Northern Hemisphere rotate **counter-clockwise** (cyclonic), whereas Southern Hemisphere cyclones rotate **clockwise**.
- **Action Plan:** In F2.3, the TCIR ingestion pipeline must filter storms by `basin == 'NI'`. If Southern Indian Ocean storms are included for pre-training, vertical/horizontal flipping must be applied to align vortex circulation direction with Northern Hemisphere Coriolis dynamics.

### 3.3 Sensor Cross-Calibration
- TCIR mosaics combine multi-satellite geostationary observations (Meteosat-7/8, INSAT, Fengyun, MTSAT).
- Calibration curves between Meteosat/GOES and INSAT-3D/3DR have known channel-response differences.
- **Action Plan:** TCIR data will be treated as an auxiliary transfer-learning / pre-training benchmark (`source_type: TCIR_EXTERNAL_BENCHMARK`), strictly partitioned from Vayumarg's primary operational INSAT test splits.

---

## 4. Controlled Ingestion Plan for F2.3

1. **Selective Extraction:** Rather than downloading the entire 60 GB global dataset, acquire only `TCIR-IO.h5` (14.2 GB) or a pre-filtered NIO subset.
2. **Metadata Cross-Verification:** Match every TCIR storm and timestamp against Vayumarg's frozen NOAA IBTrACS registry (`vayumarg_f1_1_freeze_manifest.json`) using Storm SID and observation timestamps.
3. **Database Segregation:** TCIR granules will be inserted with `ProvenanceStatus: REAL_VERIFIED`, `source_type: TCIR_ARCHIVE`, and linked to the existing `TrackObservation` records.

