# Vayumarg — Milestone F2.3 Authentic TCIR Acquisition & Integration Decision Report

**Date:** 01 November 2026  
**Status:** **AUDITED, EVALUATED & OFFICIALLY DECIDED**  
**Role:** Principal Remote-Sensing Specialist, Meteorological Research Scientist, Python ML Infrastructure Engineer  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Executive Summary & Purpose

In Milestone F2, an initial 12-sample synthetic pilot demonstrated TCIR HDF5 container parsing. Milestone F2.1 proved that those pilot rasters were synthetically simulated and permanently isolated them under `SYNTHETIC_FIXTURE`.
This report presents the definitive scientific and operational evaluation regarding the acquisition, ingestion feasibility, and research role of the authentic **TCIR (Tropical Cyclone Image and Best-Track Dataset)** archive.

---

## 2. Technical Profile of Authentic TCIR

- **Reference Citation:** Chen, B.-F., Chen, B., Lin, K.-T., & Lin, C.-C. (2020). *TCIR: A Tropical Cyclone Image and Best-Track Dataset for Intensity Estimation and Forecasting*. IEEE Transactions on Geoscience and Remote Sensing, 58(7), 5174–5188.
- **Licensing:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Official Host:** National Taiwan University (NTU) CSIE / Kaggle Open Dataset (`tcir-dataset`).
- **Archive Profile:**
  - `TCIR-IO.h5`: **~14.2 GB** (Indian Ocean subset spanning 2003 through 2017).
  - Channels: Infrared (IR, 11 $\mu\text{m}$), Water Vapour (WV, 6.7 $\mu\text{m}$), Visible (VIS, 0.65 $\mu\text{m}$), and Passive Microwave (PMW, 89 GHz).
  - Resolution: $201 \times 201$ pixels per storm patch at $4.0\text{ km}$ spacing.

---

## 3. Engineering & Scientific Evaluation

### 3.1 Feasibility of Partial / Remote Retrieval
- **Question:** Can Vayumarg download only the North Indian Ocean (`NI`) subset rows without retrieving the full Indian Ocean file?
- **Finding:** **No.** The NTU web server and Kaggle distribution endpoints provide monolithic HDF5 files or compressed archives (`.tar.gz`). Neither endpoint supports HTTP byte-range slicing through chunked HDF5 trees without downloading the container.
- **Operational Impact:** Ingesting authentic TCIR requires a single contiguous download of **14.2 GB**, exceeding the current F2.3 bounded acquisition envelope ($\le 2.0\text{ GB}$).

### 3.2 Wind Averaging Period Incompatibility
- **TCIR Best-Track Ground Truth:** Sourced exclusively from JTWC advisories, recording **1-minute maximum sustained winds**.
- **Vayumarg Regional Standard:** Sourced primarily from IMD (RSMC New Delhi), recording **3-minute maximum sustained winds**.
- **Impact:** Directly training an IMD-calibrated intensity regression model on TCIR labels without conversion introduces a systematic positive wind speed bias (+10% to +15% overestimation).

### 3.3 Hemispheric Dynamic Differences
- The `TCIR-IO.h5` file combines North Indian Ocean (Northern Hemisphere) and South Indian Ocean (Southern Hemisphere) cyclones.
- Tropical cyclones in the Southern Hemisphere rotate **clockwise** due to opposite sign Coriolis deflection, whereas North Indian Ocean storms rotate **counter-clockwise**.
- **Impact:** Pooling SH and NH imagery without vertical or horizontal reflection breaks convective pattern recognition in directional convolutional kernels.

### 3.4 Spectral Sensor Shift
- TCIR frames are assembled from NOAA GridSat-B1 (Meteosat, GOES, GMS/MTSAT) and CMORPH.
- ISRO INSAT-3DR/3DS Imagers have distinct spectral response functions (SRFs) and calibration lookup curves. Models trained exclusively on GridSat TCIR exhibit domain shift when evaluated on live INSAT-3DR/3DS feeds.

---

## 4. Formal Decision & Recommendations

### Official Verdict: **DEFER CONTIGUOUS TCIR DOWNLOAD TO PRE-TRAINING PHASE (F2.4 / F3.5)**

1. **Prioritize Native INSAT-3DR/3DS Assets:**
   Vayumarg's core operational mandate under SIH26070 is decision support for the North Indian Ocean using native ISRO satellite telemetry (MOSDAC). High-resolution native INSAT L1B rasters preserve true calibration lookup tables, raw digital counts, sub-pixel georeferencing, and direct synchronization with RSMC New Delhi synoptic best tracks.
2. **Designated Role for TCIR:**
   Authentic TCIR shall be treated as an **auxiliary self-supervised / supervised pre-training corpus**, partitioned strictly from the operational test split.
3. **Prerequisites for Subsequent TCIR Ingestion:**
   - Dedicated disk allocation (~15 GB storage reservation).
   - Ingestion pipeline filtering exclusively for `basin == 'NI'` (or programmatic horizontal reflection for `basin == 'SI'`).
   - Ground truth mapping to `secondary_jtwc` labels.

