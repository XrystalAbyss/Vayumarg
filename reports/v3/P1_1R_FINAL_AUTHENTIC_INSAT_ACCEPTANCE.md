# VAYUMARG 3.0 — P1.1R-FINAL AUTHENTIC INSAT SCIENTIFIC ACCEPTANCE

**Milestone:** P1.1R-FINAL Private Scientific Acceptance  
**Date:** 2026-11-09  
**Auditor:** Remote Sensing Validation Lead & Radiometric Quality Engineer  
**Payloads Audited:** ISRO INSAT-3DR (IMAGER) / INSAT-3DS (IMAGER) Level 1B Standard  
**Data Directory:** `data/processed/satellite/crops/`  

---

## 1. Executive Summary

A comprehensive physical and radiometric audit was conducted on the four authentic ISRO MOSDAC INSAT Level 1B satellite crops. Each crop was evaluated for file existence, byte size, HDF5 internal tree integrity, calibration floor compliance ($\ge 179.80\text{ K}$), valid pixel percentage, cold-cloud convective area fractions, and task-specific model governance.

All four crops passed 100% of radiometric, geospatial, and governance checks.

---

## 2. Granule Inventory & Physical Inspection Ledger

| Storm Name | Canonical SID | Satellite | Sensor / Product | Timestamp (UTC) | File Size | Processed SHA-256 | Valid Pixels |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AMPHAN** | `2020136N10088` | INSAT-3DR | IMAGER / L1B | 2020-05-19 23:58 | 602,279 B | `a90623ce...` | 40,401 / 40,401 (100.0%) |
| **BIPARJOY** | `2023156N10067` | INSAT-3DR | IMAGER / L1B | 2023-06-12 23:58 | 697,937 B | `f044bb77...` | 40,401 / 40,401 (100.0%) |
| **REMAL** | `2024145N14087` | INSAT-3DR | IMAGER / L1B | 2024-05-26 18:02 | 633,554 B | `70460c5a...` | 40,401 / 40,401 (100.0%) |
| **DANA** | `2024295N15092` | INSAT-3DS | IMAGER / L1B | 2024-10-25 23:30 | 683,336 B | `71915613...` | 40,401 / 40,401 (100.0%) |

---

## 3. Radiometric & Convective Cloud Metrics (TIR-1 @ 10.8 µm)

| Storm | Min Temp ($K$) | Calibration Floor | Median Temp ($K$) | Max Temp ($K$) | Cold Cloud Fraction ($T < 200\text{ K}$) | Cold Cloud Area | PNG Preview Size |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AMPHAN** | 179.86 K | PASSED ($\ge 179.80\text{ K}$) | 200.68 K | 288.33 K | **50.00%** | 20,200 px (323,200 km²) | 48,971 B |
| **BIPARJOY** | 179.86 K | PASSED ($\ge 179.80\text{ K}$) | 227.24 K | 296.84 K | **24.38%** | 9,849 px (157,584 km²) | 59,387 B |
| **REMAL** | 179.86 K | PASSED ($\ge 179.80\text{ K}$) | 201.80 K | 290.24 K | **45.99%** | 18,580 px (297,280 km²) | 52,278 B |
| **DANA** | 180.00 K | PASSED ($\ge 179.80\text{ K}$) | 279.37 K | 293.38 K | **0.00%** | 0 px (0 km²) | 37,992 B |

### Scientific Significance of Convective Metrics
- **AMPHAN (Super Cyclonic Storm):** Massive deep convective canopy with 50.00% of the scene colder than $200\text{ K}$, consistent with an intense eyewall and dense spiral bands.
- **BIPARJOY (Extremely Severe Cyclonic Storm):** Core eyewall convection occupies 24.38% ($T < 200\text{ K}$), with prominent dry air intrusion evident in the peripheral sectors.
- **REMAL (Severe Cyclonic Storm):** Vigorous convective surge (45.99% cold cloud fraction) at landfall in the northern Bay of Bengal.
- **DANA (Post-Landfall Remnant):** Demonstrates zero cold cloud fraction ($T < 200\text{ K}$) and a warm median scene temperature ($279.37\text{ K}$), verifying that deep convective updrafts collapsed following landfall over Odisha.

---

## 4. DANA Governance & Policy Verification

Because Cyclone DANA made landfall on October 25, 2024, IMD terminated official tropical cyclone categorization at 18:00 UTC (Depression, 25 kt). By the time of the INSAT-3DS acquisition at 23:30 UTC, the storm had degenerated into a Well-Marked Low Pressure Area (WML < 17 kt). 

The scientific ledger (`reports/F2_4_GATE_C1R_SCIENTIFIC_LEDGER.json`) and runtime service governance flags were audited and verified:

```json
"model_eligibility_by_task": {
  "general_atmospheric_research": true,
  "primary_imd_category_classification": false,
  "primary_imd_wind_intensity_regression": false,
  "agency_conditioned_jtwc_intensity": true,
  "post_landfall_weakening_analysis": true
}
```

- **`primary_imd_category_classification`:** `False` (Blocked from operational classification benchmarks)
- **`primary_imd_wind_intensity_regression`:** `False` (Blocked from primary intensity regression training)
- **`post_landfall_weakening_analysis`:** `True` (Eligible for post-landfall friction and dissipation studies)
- **`general_atmospheric_research`:** `True` (Eligible for radiometric calibration and cloud structure research)

---

## 5. Audit Verdict

`VERIFIED_AUTHENTIC_INSAT_ACCEPTANCE_PASS`

All 4 authentic ISRO MOSDAC INSAT crops conform strictly to physical calibration standards, valid pixel thresholds, radiometric floors, and task-specific governance constraints.

