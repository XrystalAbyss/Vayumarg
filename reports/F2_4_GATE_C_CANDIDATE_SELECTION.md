# Milestone F2.4 — Gate C Multi-Storm Candidate Selection & Scientific Trade-Off Analysis

## Executive Summary

To expand Vayumarg from a two-observation proof-of-concept into a scientifically diverse, balanced cyclone remote-sensing dataset, all candidate files in the original acquisition backlog were evaluated against strict meteorological and remote-sensing criteria:
1. Availability of verified primary IMD ground-truth labels.
2. Temporal offset relative to synoptic best-track fixes ($\le 30\text{ minutes}$, ideally $\le 15\text{ minutes}$).
3. Intensity-stage diversity (introducing high-intensity anchors).
4. Basin geographic diversity (introducing Arabian Sea representation).
5. Elimination of redundant/superfluous acquisitions.
6. Adherence to strict transfer and storage budgets ($\le 2\text{ granules}$, $\le 1.0\text{ GB}$).

---

## 1. Comprehensive Audit of Original Candidate Backlog

Five candidate granules from the original F2.3 acquisition plan remained in the catalog. Each was audited against actual PostgreSQL `track_observations` and MOSDAC metadata:

| Candidate ID | Cyclone Name | Target Acquisition (UTC) | Satellite & Product | MOSDAC gId | Nearest IMD Fix | Temporal Offset | Primary IMD Wind & Category | Scientific Priority | Final Evaluation & Rationale |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | REMAL | 2024-05-27 19:15 | INSAT-3DR `3RIMG_L1B_STD` | `13629859` | 18:00 UTC | $-75.0\text{ min}$ | 30 kt (DD) | `SECONDARY_PRIORITY` | Closest fix is 75 min away. Storm already inland over Bangladesh. We already hold authentic REMAL at peak landfall (60 kt). |
| **2** | DANA | 2024-10-25 23:08 | INSAT-3DS `3SIMG_L1B_STD` | `14514599` | 18:00 UTC | $-308.0\text{ min}$ | 25 kt (D) | `EXCLUDE_WITH_REASON` | Redundant with existing recovered DANA observation (23:30 UTC, 22-min gap). Lacks a valid primary IMD cyclone fix. |
| **3** | AMPHAN | 2020-05-19 23:15 | INSAT-3DR `3RIMG_L1B_STD` | `8353481` | 00:00 UTC | $+45.0\text{ min}$ | 95 kt (ESCS) | `SECONDARY_PRIORITY` | Valid candidate, but superseded by gId 8353650 (23:58 UTC) which has a superior 2-min synoptic alignment. |
| **4** | **AMPHAN** | **2020-05-19 23:58** | **INSAT-3DR `3RIMG_L1B_STD`** | **`8353650`** | **00:00 UTC** | **$+2.0\text{ min}$** | **95 kt (ESCS)** | **`HIGH_PRIORITY`** | **Selected as Candidate A.** Superb 2-min alignment. Pre-landfall Extremely Severe Cyclonic Storm ($95\text{ kt}$ IMD / $100\text{ kt}$ JTWC). |
| **5** | **BIPARJOY**| **2023-06-12 23:58** | **INSAT-3DR `3RIMG_L1B_STD`** | **`11789302`** | **00:00 UTC** | **$+2.0\text{ min}$** | **85 kt (VSCS)** | **`HIGH_PRIORITY`** | **Selected as Candidate B.** Superb 2-min alignment. Introduces the first authentic **Arabian Sea** observation in Vayumarg. |

---

## 2. Selected First Gate C Batch (Batch 1)

### Candidate A: Cyclone AMPHAN (Bay of Bengal)
- **MOSDAC Granule ID:** `8353650`
- **Target Filename:** `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5`
- **Satellite Platform:** INSAT-3DR (Imager Level 1B Standard)
- **Acquisition Timestamp:** `2020-05-19 23:58:00 UTC`
- **Approximate Size:** ~290 MB
- **Ground-Truth Match:**
  - Nearest Synoptic Fix: `2020-05-20 00:00:00 UTC` ($\Delta t = +2.0\text{ minutes}$)
  - Primary IMD Label: **95.0 knots** (3-min sustained), **952.0 hPa**, Category: **ESCS** (Extremely Severe Cyclonic Storm)
  - JTWC Label: **100.0 knots** (1-min sustained), **947.0 hPa**
- **Scientific Role:** Serves as a vital high-intensity anchor point (ESCS/SuCS stage) in the Bay of Bengal, providing the model with critical cloud-wall, central dense overcast (CDO), and eye structure at near-peak intensity.

### Candidate B: Cyclone BIPARJOY (Arabian Sea)
- **MOSDAC Granule ID:** `11789302`
- **Target Filename:** `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5`
- **Satellite Platform:** INSAT-3DR (Imager Level 1B Standard)
- **Acquisition Timestamp:** `2023-06-12 23:58:00 UTC`
- **Approximate Size:** ~291 MB
- **Ground-Truth Match:**
  - Nearest Synoptic Fix: `2023-06-13 00:00:00 UTC` ($\Delta t = +2.0\text{ minutes}$)
  - Primary IMD Label: **85.0 knots** (3-min sustained), **962.0 hPa**, Category: **VSCS** (Very Severe Cyclonic Storm)
  - JTWC Label: **85.0 knots** (1-min sustained), **961.0 hPa**
- **Scientific Role:** Introduces the first authentic **Arabian Sea** cyclone imagery into Vayumarg. Cross-basin representation is essential to prevent regional bias and test model robustness across differing sea-surface temperature and ambient shear regimes.

---

## 3. Strict Resource & Execution Bounds

1. **Granule Limit:** Exactly two granules (`AMPHAN` gId 8353650 and `BIPARJOY` gId 11789302).
2. **Transfer Ceiling:** Maximum transfer budget set to 1,000 MB. Estimated required transfer: ~581 MB.
3. **Execution Policy:** Sequential single-stream transfers with HTTP Range verification and exponential backoff retry caps.
4. **No Premature Execution:** In compliance with project governance, execution is paused pending explicit owner approval.

