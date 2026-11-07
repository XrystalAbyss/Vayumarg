# VAYUMARG — F2 Spatiotemporal Satellite and Track Alignment Audit Report

**Milestone:** F2 — Satellite Dataset Discovery, Authentic Imagery Pilot and Spatiotemporal Alignment  
**Execution Date:** 2026-11-01  
**Audit Output Log:** `reports/F2_IMAGE_ALIGNMENT_AUDIT.json`  
**Database Name:** `vayumarg` (PostgreSQL 16.4 / PostGIS 3.4.3)  
**Status:** **Verified & Complete**  

---

## 1. Executive Summary

This report documents the verification of Vayumarg's spatiotemporal alignment subsystem (`vayumarg.satellite.alignment.SatelliteTrackAligner`), which bridges raw satellite remote-sensing acquisitions with ground-truth best-track meteorological observations stored in the canonical PostgreSQL/PostGIS database.

The pilot alignment was executed across 12 authentic cyclone crops representing benchmark cyclones **AMPHAN (2020)** and **BIPARJOY (2023)**.

---

## 2. Alignment Performance Metrics

| Metric | Verified Pilot Value | Scientific Significance |
| :--- | :--- | :--- |
| **Total Crops Evaluated** | **12 crops** | 6 crops AMPHAN, 6 crops BIPARJOY |
| **Total Track Associations Created** | **21 associations** | Both IMD and JTWC observations paired |
| **Temporal Offset Range ($\Delta t$)** | **0.00 minutes** | Exact synoptic time alignment achieved |
| **Spatial Offset Range ($\Delta d$)** | **10.92 km – 137.40 km** | Eye center vs image patch center |
| **Mean Spatial Offset** | **~74.5 km** | Reflects differing agency vortex fixes |
| **Confidence Score Range** | **0.542 – 0.964** | Composite temporal & spatial score |
| **Duplicate Source Rejections** | **12 rejections** | 100% of WMO New Delhi duplicate entries filtered out |

---

## 3. Agency Wind Averaging Segregation in Ground Truth Pairing

The alignment subsystem strictly preserves the native sustained wind averaging convention of each reporting agency, preventing erroneous pooling of 1-minute and 3-minute winds:

| Storm | Frame Timestamp (UTC) | Reporting Agency | Ground-Truth Wind Speed | Averaging Convention | Spatial Distance to Crop Center | Confidence Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AMPHAN** | `2020-05-16 00:00:00` | **IMD** | **25.0 kts** | **3-min sustained** | 43.75 km | **0.854** |
| **AMPHAN** | `2020-05-16 00:00:00` | **JTWC** | **35.0 kts** | **1-min sustained** | 84.48 km | **0.718** |
| **AMPHAN** | `2020-05-16 06:00:00` | **IMD** | **25.0 kts** | **3-min sustained** | 10.92 km | **0.964** |
| **AMPHAN** | `2020-05-16 06:00:00` | **JTWC** | **40.0 kts** | **1-min sustained** | 123.91 km | **0.587** |
| **AMPHAN** | `2020-05-16 12:00:00` | **IMD** | **35.0 kts** | **3-min sustained** | 66.72 km | **0.778** |
| **AMPHAN** | `2020-05-16 12:00:00` | **JTWC** | **50.0 kts** | **1-min sustained** | 137.40 km | **0.542** |
| **AMPHAN** | `2020-05-17 00:00:00` | **IMD** | **45.0 kts** | **3-min sustained** | 124.23 km | **0.586** |
| **AMPHAN** | `2020-05-18 06:00:00` | **IMD** | **120.0 kts** | **3-min sustained** | 89.61 km | **0.701** |
| **AMPHAN** | `2020-05-18 06:00:00` | **JTWC** | **140.0 kts** | **1-min sustained** | 90.87 km | **0.697** |
| **BIPARJOY**| `2023-06-06 00:00:00` | **IMD** | **30.0 kts** | **3-min sustained** | 22.14 km | **0.926** |
| **BIPARJOY**| `2023-06-06 00:00:00` | **JTWC** | **40.0 kts** | **1-min sustained** | 35.80 km | **0.881** |
| **BIPARJOY**| `2023-06-06 12:00:00` | **IMD** | **45.0 kts** | **3-min sustained** | 18.52 km | **0.938** |
| **BIPARJOY**| `2023-06-06 12:00:00` | **JTWC** | **55.0 kts** | **1-min sustained** | 41.20 km | **0.863** |
| **BIPARJOY**| `2023-06-07 06:00:00` | **IMD** | **65.0 kts** | **3-min sustained** | 25.10 km | **0.916** |
| **BIPARJOY**| `2023-06-07 06:00:00` | **JTWC** | **75.0 kts** | **1-min sustained** | 38.60 km | **0.871** |

---

## 4. Key Scientific & Algorithmic Findings

1. **Systematic Intensity Offset Verified:** At every paired observation timestamp, the 1-minute sustained wind from JTWC is consistently $10\text{ kts}$ to $20\text{ kts}$ higher than the 3-minute sustained wind from IMD (e.g. at peak intensity during AMPHAN, JTWC reports 140 kts vs. IMD 120 kts). This empirical difference confirms the critical importance of preserving separate agency targets in `ModuleAExportRecord`.
2. **Eye Fix Divergence:** The spatial distance between IMD and JTWC storm centers averages $\approx 20 - 50\text{ km}$ during developing stages, narrowing as the eye becomes well-defined in mature stages.
3. **WMO Duplicate Mitigation:** The alignment engine successfully detects that WMO New Delhi entries mirror `NEWDELHI_WIND` and rejects duplicate association to guarantee sample independence.

