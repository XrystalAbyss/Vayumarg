# Vayumarg — Milestone F2.3 Image-to-Label Alignment & Scientific Governance Report

**Date:** 01 November 2026  
**Status:** **AUDITED, STANDARDIZED & ENFORCED**  
**Role:** Meteorological Research Scientist, Geospatial Specialist, Database Architect  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Executive Summary

A critical vulnerability identified in preliminary cyclone ML projects is spatial-temporal mismatch and label duplication between satellite rasters and historical best tracks. 
This report specifies the alignment protocol, multi-agency label segregation, and deduplication rules enforced across Vayumarg's scientific foundation.

---

## 2. Spatio-Temporal Association Protocol

For every authentic satellite granule, alignment to historical best-track observations proceeds through a rigorous 5-step gating process:

```
Step 1: Extract Granule Midpoint Timestamp: t_obs = t_start + (t_end - t_start) / 2
   │
   ▼
Step 2: Match Storm by Canonical Name and Season Year
   │
   ▼
Step 3: Query TrackObservation for |t_track - t_obs| <= 60 minutes
   │
   ▼
Step 4: Resolve Primary Agency (IMD, RSMC New Delhi)
        - Extract (lat_imd, lon_imd), wind_kt_imd (3-min mean), central_pressure_hpa
   │
   ▼
Step 5: Resolve Secondary Agency (JTWC)
        - Extract (lat_jtwc, lon_jtwc), wind_kt_jtwc (1-min mean), central_pressure_hpa
        - Compute inter-agency distance offset: Delta_d = geodesic_distance(pos_imd, pos_jtwc)
```

---

## 3. Strict Sample Deduplication Invariant

In relational databases, querying `satellite_processed_crops` joined with `satellite_track_associations` creates multiple rows if an image is associated with both IMD and JTWC observations.
- **Vayumarg Guarantee:** The export contract [`export_module_a_multichannel_dataset`](file:///c:/Users/astra/Desktop/Project/Vayumarg/src/vayumarg/contracts/export.py) groups associations by `crop_id`.
- **Atomic Sample Model:** Exactly **1 sample record per image crop**.
- Primary agency (IMD) and secondary agency (JTWC) labels are encapsulated within the same sample object, eliminating duplicate frames from training batches.

---

## 4. Multi-Agency Wind Standards & Conversion Caveats

- **IMD (RSMC New Delhi):** Standard wind speed is the **3-minute sustained wind**.
- **JTWC (Joint Typhoon Warning Center):** Standard wind speed is the **1-minute sustained wind**.
- **Conversion Factor:** Under Atkinson & Holliday (1977) empirical conversions adapted for tropical cyclones:
  $$V_{1\text{-min}} \approx 1.14 \times V_{3\text{-min}} \quad \text{or} \quad V_{3\text{-min}} \approx 0.88 \times V_{1\text{-min}}$$
- **Governance Rule:** Vayumarg **never applies scalar wind speed conversions implicitly**. The original reported values are preserved in separate fields (`labels.primary_imd.wind_kt` and `labels.secondary_jtwc.wind_kt`), allowing ML model architects to train dual-head loss functions or select single-agency targets transparently.

