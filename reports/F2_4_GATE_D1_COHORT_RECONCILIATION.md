# Vayumarg F2.4 Gate D1 — Cohort Count & Canonical SID Reconciliation Report

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate D1 — Balanced Acquisition Selection & First-Batch Preflight  
**Auditor:** Principal Scientific Data Architect, Dataset Sampling Specialist, QA Lead  
**Audit Target:** Reconciliation of Reported 14 vs 15 Storm Discrepancy & Canonical SID Accounting  
**Outcome Classification:** **`REPORTING_ARITHMETIC_ERROR_RESOLVED`**  

---

## 1. Background of the Discrepancy

Milestone F2.4 Gate C1R documented:
- 4 existing unique cyclone events.
- 11 additional distinct cyclone events.
- *14 distinct cyclone events overall in the planned 18-granule cohort.*

As noted by the QA audit lead, this stated arithmetic ($4 + 11 = 14$) is contradictory. An exhaustive forensic review was conducted across all candidate canonical IBTrACS SIDs to resolve the exact arithmetic and clarify the entity hierarchy.

---

## 2. Canonical IBTrACS SID Audit

### 2.1 Previously Acquired Storm SIDs ($N=4$)

| Cyclone Name | Season | Basin | Canonical IBTrACS SID | Satellite Platform | Status |
|---|---|---|---|---|---|
| **REMAL** | 2024 | Bay of Bengal | `2024145N14087` | INSAT-3DR | Acquired & Verified |
| **DANA** | 2024 | Bay of Bengal | `2024295N15092` | INSAT-3DS | Acquired & Verified |
| **AMPHAN** | 2020 | Bay of Bengal | `2020136N10088` | INSAT-3DR | Acquired & Verified |
| **BIPARJOY**| 2023 | Arabian Sea | `2023156N10067` | INSAT-3DR | Acquired & Verified |

### 2.2 Proposed Candidate Granules ($N=14$)

| # | Candidate ID | Storm Name | Season | Canonical IBTrACS SID | Basin | Platform | New or Repeated SID? |
|---|---|---|---|---|---|---|---|
| 1 | `GATE_D_CAND_01` | **FANI** | 2019 | `2019116N02090` | BoB | INSAT-3DR | **NEW SID** |
| 2 | `GATE_D_CAND_02` | **BULBUL** | 2019 | `2019302N11118` | BoB | INSAT-3DR | **NEW SID** |
| 3 | `GATE_D_CAND_03` | **NISARGA** | 2020 | `2020153N13072` | AS | INSAT-3DR | **NEW SID** |
| 4 | `GATE_D_CAND_04` | **TAUKTAE** | 2021 | `2021133N10071` | AS | INSAT-3DR | **NEW SID** |
| 5 | `GATE_D_CAND_05` | **YAAS** | 2021 | `2021143N15090` | BoB | INSAT-3DR | **NEW SID** |
| 6 | `GATE_D_CAND_06` | **ASANI** | 2022 | `2022126N07095` | BoB | INSAT-3DR | **NEW SID** |
| 7 | `GATE_D_CAND_07` | **MANDOUS** | 2022 | `2022338N05100` | BoB | INSAT-3DR | **NEW SID** |
| 8 | `GATE_D_CAND_08` | **MOCHA** | 2023 | `2023129N08091` | BoB | INSAT-3DR | **NEW SID** |
| 9 | `GATE_D_CAND_09` | **MICHAUNG** | 2023 | `2023334N08088` | BoB | INSAT-3DR | **NEW SID** |
| 10| `GATE_D_CAND_10` | **ASNA** | 2024 | `2024238N25077` | AS | INSAT-3DS | **NEW SID** |
| 11| `GATE_D_CAND_11` | **FENGAL** | 2024 | `2024329N04089` | BoB | INSAT-3DS | **NEW SID** |
| 12| `GATE_D_CAND_12` | **TAUKTAE_EARLY** | 2021 | `2021133N10071` | AS | INSAT-3DR | Repeated (Matches Cand 04) |
| 13| `GATE_D_CAND_13` | **MOCHA_EARLY** | 2023 | `2023129N08091` | BoB | INSAT-3DR | Repeated (Matches Cand 08) |
| 14| `GATE_D_CAND_14` | **REMAL_DEV** | 2024 | `2024145N14087` | BoB | INSAT-3DR | **Repeated (Matches Existing REMAL)** |

---

## 3. Exact Mathematical Reconciliation

$$\begin{aligned}
\text{Previously Acquired Storm SIDs} &= 4 \\
\text{Proposed Additional Granules} &= 14 \\
\text{Unique SIDs in Candidate Cohort} &= 12 \\
\text{Previously Represented SIDs Repeated in Candidates} &= 1 \quad (\text{Cyclone REMAL: } 2024145\text{N}14087) \\
\text{Newly Introduced Storm SIDs} &= 11 \\
\text{Total Unique Storm SIDs in 18-Granule Cohort} &= 4 + 11 = \mathbf{15}
\end{aligned}$$

### Root Cause of the Reported Discrepancy
The figure "14 distinct cyclones" in Gate C1R prose was an inadvertent mental arithmetic slip. The author counted the 14 candidate granules and assumed 14 unique storms total, or subtracted the 1 repeated existing storm (`REMAL_DEV`) from 15 without updating the summary text.

**The actual inventory structure is 100% sound:**
- **Total Planned Granules:** 18
- **Total Unique Cyclone Events (Canonical SIDs):** Exactly **15**
- **Storms with 2 Granules (Longitudinal Pairs):** 3 storms (`REMAL`, `TAUKTAE`, `MOCHA`)
- **Storms with 1 Granule (Single Frames):** 12 storms (`DANA`, `AMPHAN`, `BIPARJOY`, `FANI`, `BULBUL`, `NISARGA`, `YAAS`, `ASANI`, `MANDOUS`, `MICHAUNG`, `ASNA`, `FENGAL`)

---

## 4. Cohort Composition Across Diversity Axes

### 4.1 Granules per Basin ($N=18$)
- **Bay of Bengal:** 13 granules (72.2%) across 10 unique storms
- **Arabian Sea:** 5 granules (27.8%) across 5 unique storms (`BIPARJOY`, `NISARGA`, `TAUKTAE`, `ASNA`, `TAUKTAE_EARLY`)

### 4.2 Granules per Satellite Platform ($N=18$)
- **INSAT-3DR:** 15 granules (83.3%)
- **INSAT-3DS:** 3 granules (16.7%) (`DANA`, `ASNA`, `FENGAL`)

---

## 5. Strict Entity Hierarchy Definitions

To ensure scientific clarity in all documentation and automated code:
1. **Planned Source Granules ($N=18$):** The number of discrete L1B standard HDF5 files downloaded from SAC/ISRO MOSDAC.
2. **Unique Satellite Acquisitions ($N=18$):** The number of distinct observation timestamps recorded by INSAT instruments.
3. **Unique Cyclone Events ($N=15$):** The number of distinct, internationally registered tropical cyclones (unique NOAA IBTrACS SIDs).
4. **Image-Label Associations:** The number of relational links in PostgreSQL table `satellite_track_associations` (e.g. 10 associations across the current 4 images; ~45 associations across the full 18-granule cohort).
5. **Independently Eligible Supervised Examples:** The deduplicated sample count grouped strictly by `crop_id` (1 image = 1 sample).

