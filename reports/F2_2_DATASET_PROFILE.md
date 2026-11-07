# Vayumarg — Milestone F2.2 Scientific Dataset Profile Report

**Date:** 01 November 2026  
**Status:** AUDITED & SCIENTIFICALLY PROFILED  
**Author:** Principal Meteorological Data Scientist & Data Quality Auditor  
**Milestone:** F2.2 (Scientific Dataset Readiness)

---

## 1. Overview & Inventory Summary

As of the conclusion of Milestone F2.2, Vayumarg's scientific data foundation integrates an authoritative historical cyclone track registry with verified, multi-channel geostationary satellite imagery.

### 1.1 Complete Database Inventory

| Data Domain | Entity Type | Count | Status / Provenance |
| :--- | :--- | :--- | :--- |
| **Meteorological Best Track** | Unique Tropical Storms | **1,860** | Frozen (NOAA IBTrACS v04r01 NI basin) |
| | Synoptic Track Observations | **104,374** | Frozen (1842–2024, IMD & JTWC dual-track) |
| **Satellite Platform Catalog** | Satellite Sensor Products | **10** | Registered (INSAT-3D, 3DR, 3DS, TCIR) |
| **Physical Satellite Granules** | Raw L1B Full Disks | **2** | 1 REAL_VERIFIED (280.6 MB), 1 SYNTHETIC_PILOT |
| **Spatial Image Crops** | Extracted Cyclone Patches | **13** | 1 REAL_VERIFIED Multi-channel (618 KB), 12 SYNTHETIC_PILOT |
| **Spatio-Temporal Links** | Track Associations | **23** | 2 REAL_VERIFIED (Dual IMD/JTWC), 21 SYNTHETIC_PILOT |
| **Remote Catalog Discovery** | MOSDAC Candidate Granules | **2,173** | Inventoried across REMAL, DANA, AMPHAN, BIPARJOY |

---

## 2. Multi-Channel Sensor Specifications

| Channel | Wavelength ($\mu\text{m}$) | Native Spatial Resolution | Resampled Grid | Temperature / Calibration Range | Saturation Floor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IMG_TIR1** | 10.8 | 4.0 km | $201 \times 201$ (Native) | $179.86\text{ K}$ – $340.06\text{ K}$ | $179.86\text{ K}$ (Count $\ge 921$) |
| **IMG_WV** | 6.8 | 8.0 km | $201 \times 201$ (Bilinear) | $179.69\text{ K}$ – $300.00\text{ K}$ | $179.69\text{ K}$ (Count $\ge 995$) |
| **Spatial Window**| — | $800\text{ km} \times 800\text{ km}$ | Fixed Cartesian Grid | — | — |

---

## 3. Dataset Attrition & Quality Funnel

To ensure high model generalization and prevent training on degraded or uncalibrated imagery, Vayumarg implements a 5-stage attrition funnel:

```
Stage 1: Raw MOSDAC Full Disk Granules (2,173 Candidates)
   │
   ▼  [Filter: Spatial Intersection with NIO Best-Track Fix within ±30 min]
Stage 2: Matched Candidate Granules (~450 Potential Intersections)
   │
   ▼  [Filter: Successful Acquisition & Checksum Validation]
Stage 3: Verified Raw HDF5 Assets (On-disk)
   │
   ▼  [Filter: 800 km Box inside Valid Earth Disk; Non-fill > 80%]
Stage 4: Extracted Multi-Channel Crops (TIR-1 + WV Co-registered)
   │
   ▼  [Filter: Radiometric Calibration Valid; Agency Label Verified]
Stage 5: Train / Test Eligible Samples (Module A Training Tensor)
```

---

## 4. Leakage Prevention & Normalization Governance

1. **Temporal Storm-Level Partitioning:** Splits between training, validation, and testing must be split **by storm SID**, never by random frame sampling. Splitting frames from the same storm across train and test sets creates massive data leakage due to high temporal autocorrelation between consecutive 30-minute images.
2. **Train-Only Normalization Statistics:** All feature scaling (mean, standard deviation, min-max bounds) must be computed exclusively on the training split and stored in a versioned scaler artifact. Applying dataset-wide normalization across test splits is strictly forbidden.

