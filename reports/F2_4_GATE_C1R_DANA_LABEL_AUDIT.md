# Vayumarg F2.4 Gate C1R — Cyclone DANA Label Eligibility & IMD Status Audit

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate C1R — Scientific Metadata Closure & Gate D Preflight  
**Auditor:** Meteorological Research Scientist, Remote-Sensing Engineer, QA Lead  
**Audit Scope:** Late-Stage DANA Image Calibration, IMD Downgrade Status, and Multi-Task Eligibility  
**Status:** **RECONCILED & ELIGIBILITY CONSTRAINTS REAFFIRMED**  

---

## 1. Meteorological Context & Agency Divergence

The authentic Cyclone DANA granule (`3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5`, INSAT-3DS) captured the storm at `2024-10-25 23:30:12` to `23:34:29 UTC`, approximately 22 hours post-landfall over northern Odisha.

At the nearest synoptic evaluation time (`2024-10-26 00:00:00 UTC`):
- **IMD Status:** The India Meteorological Department (IMD) officially declared that Cyclone DANA had weakened from a Depression ($25\text{ kt}$ at 18:00 UTC) into a **Well Marked Low Pressure Area (WML)** with maximum sustained surface winds $< 17\text{ kt}$. Consequently, IMD ceased issuing formal cyclonic best-track advisories.
- **JTWC Status:** The Joint Typhoon Warning Center (JTWC) maintained an overland track fix at $21.2^\circ\text{N}$, $86.4^\circ\text{E}$ with 1-minute sustained winds of **20 kt** ($10.3\text{ m/s}$) and central pressure of **1000 hPa**.

---

## 2. Database Evidence & Track Association Reality

A direct audit of the PostgreSQL research database demonstrates:
1. **Zero IMD Associations for DANA:** In `satellite_track_associations`, the DANA crop (`869cd46b-659a-430a-8a45-d2fd8ad7174b`) links strictly to:
   - `Assoc 6ad0d070-...`: JTWC (`TrackObservation` 20 kt, 1000 hPa, 1-min averaging).
   - `Assoc 07c83a9e-...`: IBTRACS (`TrackObservation` Wind=None, Pres=None).
   - **No IMD track association exists for DANA at 2024-10-26 00:00 UTC.**
2. **Pre-Existing QC Isolation:** In `SatelliteProcessedCrop.quality_control_flags`, the DANA metadata dictionary already contained explicit task-level eligibility flags:
   ```json
   {
     "general_atmospheric_research": true,
     "post_landfall_weakening_analysis": true,
     "agency_conditioned_jtwc_intensity": true,
     "primary_imd_category_classification": false,
     "primary_imd_wind_intensity_regression": false,
     "ineligibility_reasons": [
       "Primary IMD best-track cyclonic classification terminated at 18:00 UTC (Depression, 25 kt). By 00:00 UTC 26 Oct 2024, IMD documented DANA weakened into a Well Marked Low Pressure Area (WML < 17 kt), ending official cyclone categorization."
     ]
   }
   ```

---

## 3. Discrepancy Resolution: The "4 IMD Associations" Claim

In the earlier Gate C Batch 1 report narrative, the text inadvertently referred to "4 IMD associations" by informally conflating the 4 authentic storms with 4 IMD targets. 

The audit clarifies:
- **There were NEVER 4 IMD associations in PostgreSQL.** There were exactly 3 IMD associations (REMAL, AMPHAN, BIPARJOY).
- DANA was correctly preserved as an authentic physical imagery asset (`REAL_VERIFIED`) without inventing a non-existent IMD cyclonic label.

---

## 4. Authentic Imagery Corpus Eligibility Ledger

| Category / Metric | Verified Count | Represented Cyclones & Details |
|---|---|---|
| **Authentic Physical Images** | **4** | REMAL, DANA, AMPHAN, BIPARJOY |
| **Images with ANY IMD Historical Association** | **3** | REMAL, AMPHAN, BIPARJOY (DANA excluded) |
| **Images Eligible for Primary IMD Category Target** | **3** | REMAL (SCS), AMPHAN (ESCS), BIPARJOY (VSCS) |
| **Images Eligible for Primary IMD Wind Target** | **3** | REMAL (60 kt), AMPHAN (95 kt), BIPARJOY (85 kt) |
| **Images Eligible for Secondary JTWC Target** | **4** | REMAL (55 kt), DANA (20 kt), AMPHAN (100 kt), BIPARJOY (85 kt) |
| **Images with No Suitable Supervised Target** | **0** | All 4 images possess valid, rigorously bounded research targets |

---

## 5. Governance Directive for Module A Training

1. When training the **Primary IMD Cyclone Intensity Estimator**, DANA **MUST BE EXCLUDED** via query filter `WHERE (quality_control_flags->'model_eligibility'->>'primary_imd_category_classification')::boolean = true`.
2. When training **Multi-Task Overland Weakening / Dissipation Models** or **JTWC Cross-Agency Models**, DANA **IS FULLY ELIGIBLE**.
3. Source authenticity (`REAL_VERIFIED`) remains strictly decoupled from task-specific label eligibility.

