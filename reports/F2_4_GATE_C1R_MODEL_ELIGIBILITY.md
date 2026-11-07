# Vayumarg F2.4 Gate C1R — Multi-Dimensional Model Eligibility Matrix

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate C1R — Scientific Metadata Closure & Gate D Preflight  
**Auditor:** Meteorological Data Scientist, ML Dataset Architect, Independent QA Lead  
**Scope:** Supervised Task Definitions, Label Conditioning, and Training Set Eligibility Rules  
**Status:** **FORMALIZED & READY FOR ML PIPELINE INTEGRATION**  

---

## 1. Executive Summary

To prevent data leakage, unphysical label mixing, and training corruption in Module A, Vayumarg strictly dissociates **data asset authenticity** (`verification_status = 'REAL_VERIFIED'`) from **task-specific supervised eligibility**.

Every authentic crop in Vayumarg is evaluated across five distinct scientific machine learning tasks:
- **Task A1:** Primary IMD Wind Intensity Regression (3-minute sustained wind, continuous $kt$).
- **Task A2:** Primary IMD Cyclone Category Classification (Discrete IMD Scale: D, DD, CS, SCS, VSCS, ESCS, SuCS).
- **Task A3:** Agency-Conditioned JTWC Wind Intensity Regression (1-minute sustained wind, continuous $kt$).
- **Task A4:** Post-Landfall Weakening & Overland Dissipation Analysis.
- **Task A5:** Unsupervised / Self-Supervised Atmospheric Feature Representation Learning.

---

## 2. Multi-Task Eligibility Matrix

| Field / Metric | Crop 1: REMAL | Crop 2: DANA | Crop 3: AMPHAN | Crop 4: BIPARJOY |
|---|---|---|---|---|
| **Crop UUID** | `e93002d6-a5e2...` | `869cd46b-659a...` | `142da9e9-417e...` | `fc074478-42dd...` |
| **Storm & Season** | REMAL (2024) | DANA (2024) | AMPHAN (2020) | BIPARJOY (2023) |
| **Basin** | Bay of Bengal | Bay of Bengal | Bay of Bengal | Arabian Sea |
| **Satellite Platform** | INSAT-3DR | INSAT-3DS | INSAT-3DR | INSAT-3DR |
| **Nominal Acquisition** | `2024-05-26 18:02` | `2024-10-25 23:30` | `2020-05-19 23:58` | `2023-06-12 23:58` |
| **IMD Wind Target** | **60.0 kt** | **NULL** | **95.0 kt** | **85.0 kt** |
| **IMD Category Target** | **SCS** | **NULL** | **ESCS** | **VSCS** |
| **JTWC Wind Target** | **55.0 kt** | **20.0 kt** | **100.0 kt** | **85.0 kt** |
| **Task A1 (IMD Wind)** | **ELIGIBLE** | **INELIGIBLE** | **ELIGIBLE** | **ELIGIBLE** |
| **Task A2 (IMD Cat)** | **ELIGIBLE** | **INELIGIBLE** | **ELIGIBLE** | **ELIGIBLE** |
| **Task A3 (JTWC Wind)** | **ELIGIBLE** | **ELIGIBLE** | **ELIGIBLE** | **ELIGIBLE** |
| **Task A4 (Weakening)**| Ineligible (Ocean) | **ELIGIBLE** | Ineligible (Ocean) | Ineligible (Ocean) |
| **Task A5 (Pretraining)**| **ELIGIBLE** | **ELIGIBLE** | **ELIGIBLE** | **ELIGIBLE** |
| **Ineligibility Reason** | None | Downgraded to WML (<17 kt) by IMD | None | None |

---

## 3. Detailed Task Definitions & Conditioning Protocols

### 3.1 Task A1: Primary IMD Wind Speed Regression
- **Target Variable:** `TrackObservation.wind_speed_knots` where `source_agency = 'IMD'` and `averaging_period = '3-min'`.
- **Loss Function:** Root Mean Squared Error (RMSE) / Mean Absolute Error (MAE).
- **Eligible Samples (N=3):** REMAL ($60\text{ kt}$), AMPHAN ($95\text{ kt}$), BIPARJOY ($85\text{ kt}$).
- **Exclusion Rule:** DANA is strictly excluded because IMD ceased issuing cyclonic wind estimates at this synoptic time.

### 3.2 Task A2: Primary IMD Cyclone Category Classification
- **Target Variable:** `TrackObservation.imd_category` (Ordinal: `Depression` to `Super Cyclonic Storm`).
- **Loss Function:** Cross-Entropy / Focal Loss.
- **Eligible Samples (N=3):** REMAL (`SCS`), AMPHAN (`ESCS`), BIPARJOY (`VSCS`).
- **Exclusion Rule:** DANA is excluded because WML is an overland remnant state below official cyclonic storm classification.

### 3.3 Task A3: Agency-Conditioned JTWC Intensity Regression
- **Target Variable:** `TrackObservation.wind_speed_knots` where `source_agency = 'JTWC'` and `averaging_period = '1-min'`.
- **Conditioning Token:** Model must accept an explicit agency embedding token (e.g., `agency=JTWC`) to prevent bias contamination against 3-minute IMD targets.
- **Eligible Samples (N=4):** All 4 authentic crops are eligible: REMAL ($55\text{ kt}$), DANA ($20\text{ kt}$), AMPHAN ($100\text{ kt}$), BIPARJOY ($85\text{ kt}$).

### 3.4 Task A4: Post-Landfall Weakening & Overland Dissipation Analysis
- **Focus:** Modeling the rapid degradation of deep convection and central dense overcast over land.
- **Eligible Samples (N=1):** DANA is an exceptional, high-resolution INSAT-3DS case study captured 22 hours after Odisha landfall.

### 3.5 Task A5: Unsupervised / Self-Supervised Atmospheric Feature Learning
- **Focus:** Masked Autoencoder (MAE), Contrastive Learning, or Variational Autoencoder (VAE) representation learning across physical brightness temperature arrays.
- **Eligible Samples (N=4):** All 4 crops are 100% physically valid, calibrated, and eligible.

---

## 4. Queryable SQL Filtering Patterns for ML Data Loaders

To guarantee that downstream data pipelines never accidentally incorporate ineligible samples:

```sql
-- 1. Extract Strictly Eligible Samples for Primary IMD Models (Tasks A1 & A2)
SELECT 
    c.id AS crop_id,
    c.storage_uri,
    o.wind_speed_knots AS imd_wind_kt,
    o.imd_category AS imd_category
FROM satellite_processed_crops c
JOIN satellite_track_associations a ON a.crop_id = c.id
JOIN track_observations o ON o.id = a.track_observation_id
WHERE c.verification_status = 'REAL_VERIFIED'
  AND a.verification_status = 'REAL_VERIFIED'
  AND o.source_agency = 'IMD'
  AND (c.quality_control_flags->'model_eligibility'->>'primary_imd_category_classification')::boolean = true;

-- 2. Extract Eligible Samples for Agency-Conditioned JTWC Models (Task A3)
SELECT 
    c.id AS crop_id,
    c.storage_uri,
    o.wind_speed_knots AS jtwc_wind_kt
FROM satellite_processed_crops c
JOIN satellite_track_associations a ON a.crop_id = c.id
JOIN track_observations o ON o.id = a.track_observation_id
WHERE c.verification_status = 'REAL_VERIFIED'
  AND a.verification_status = 'REAL_VERIFIED'
  AND o.source_agency = 'JTWC'
  AND (c.quality_control_flags->'model_eligibility'->>'agency_conditioned_jtwc_intensity')::boolean = true;
```

