# Vayumarg — Milestone F2.3 Scientific Dataset Profile Report

**Date:** 01 November 2026  
**Status:** **AUDITED, STANDARDIZED & PROFILED**  
**Role:** Principal Meteorological Data Scientist & Data Quality Auditor  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Foundation Inventory & Scale Summary

Vayumarg's shared scientific repository integrates comprehensive historical cyclone best tracks with verified multi-spectral geostationary satellite telemetry.

### 1.1 Complete Database Inventory

| Data Domain | Entity Type | Count | Scientific Status / Governance |
| :--- | :--- | :--- | :--- |
| **Meteorological Best Track** | Unique Tropical Storms | **1,860** | Frozen (NOAA IBTrACS v04r01 NI basin, 1842–2024) |
| | Synoptic Track Observations | **104,374** | Frozen (IMD 3-min & JTWC 1-min dual-track records) |
| **Satellite Platform Catalog** | Satellite Sensor Products | **10** | Registered (INSAT-3D, 3DR, 3DS L1B/L1C, TCIR) |
| **Physical Satellite Granules** | Authentic Raw L1B Full Disks | **Multiple** | `REAL_VERIFIED` (ISRO MOSDAC, 10-bit HDF5) |
| | Synthetic Test Fixtures | **1** | `SYNTHETIC_FIXTURE` (Quarantined from ML datasets) |
| **Multi-Channel Processed Crops**| Authentic Extracted Crops | **Multiple** | `REAL_VERIFIED` ($800\text{ km} \times 800\text{ km}$, 618 KB/crop) |
| | Synthetic Pilot Crops | **12** | `SYNTHETIC_FIXTURE` (Quarantined) |
| **Spatio-Temporal Associations** | Authentic Track Links | **Multiple** | `REAL_VERIFIED` (Dual-agency IMD/JTWC alignment) |
| | Synthetic Fixture Links | **21** | `SYNTHETIC_FIXTURE` (Quarantined) |

---

## 2. Multi-Channel Sensor Specifications

| Channel Name | Central Wavelength ($\mu\text{m}$) | Native Nadir Resolution | Co-registered Matrix | Calibrated Physical Unit | Saturation Floor ($K$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IMG_TIR1** | 10.8 | 4.0 km | $201 \times 201$ | Brightness Temperature ($K$) | $179.86\text{ K}$ ($c \ge 921$) |
| **IMG_WV** | 6.8 | 8.0 km | $201 \times 201$ | Brightness Temperature ($K$) | $179.69\text{ K}$ ($c \ge 995$) |
| **Physical Window** | — | Fixed $800\text{ km} \times 800\text{ km}$ | $201 \times 201$ | Standardized Cartesian Grid | — |

---

## 3. Dataset Representation Across Lifecycle Stages & Basins

The multi-storm acquisition cohort was architected to span distinct meteorological regimes:

1. **Weak / Dissipation Regime:** Cyclone REMAL (May 2024) — inland post-landfall dissipation over northeast India.
2. **Next-Generation Sensor Calibration:** Cyclone DANA (Oct 2024) — INSAT-3DS operational Imager payload validation during Odisha landfall.
3. **Rapid Scan Temporal Delta:** Cyclone DANA (Oct 2024) — consecutive rapid acquisitions separated by 22 minutes, enabling cloud-top expansion rate analysis.
4. **Catastrophic Super-Cyclone Convection:** Cyclone AMPHAN (May 2020) — Category 5 equivalent Super Cyclonic Storm with extensive convective overcast colder than $180\text{ K}$.
5. **Western Basin Dynamics:** Cyclone BIPARJOY (June 2023) — long-lived Extremely Severe Cyclonic Storm in the Arabian Sea, providing essential geographical diversity.

