# Vayumarg F2.4 Gate D — Authentic Satellite Selection Strategy & Balanced Cohort Architecture

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate D Preflight  
**Architect:** Principal Scientific Data Architect, Meteorological Research Scientist, Remote-Sensing Specialist  
**Cohort Ceiling:** 18 Authentic Granules (4 Verified Existing + 14 Candidate Granules)  
**Status:** **GATE_D_READY_FOR_APPROVAL (PRE-DOWNLOAD METADATA BLUEPRINT)**  

---

## 1. Scientific Strategy & Core Principles

The objective of **Gate D** is to expand Vayumarg's authentic satellite corpus from 4 granules to a robust, diverse 18-granule research cohort without wasting network bandwidth on redundant frames.

Rather than sampling arbitrary snapshots from a single storm or popular cyclone, the Gate D cohort is engineered around six orthogonal diversity axes:
1. **Basin Balance:** Covering both the Bay of Bengal (BoB) and the Arabian Sea (AS).
2. **Dynamic Intensity Coverage:** Spanning weak systems (Depressions, $20-25\text{ kt}$) to catastrophic systems (Extremely Severe / Super Cyclonic Storms, $> 100\text{ kt}$).
3. **Sensor Platform Representation:** Bridging the workhorse **INSAT-3DR** (2019–2023) and ISRO's newest 3rd-generation **INSAT-3DS** (2024).
4. **Storm Life-Cycle Diversity:** Capturing initial cyclogenesis/intensification, peak intensity, and post-landfall dissipation.
5. **Geographical & Coastal Diversity:** Systems making landfall or impacting Gujarat, Maharashtra, Odisha, West Bengal, Andhra Pradesh, and Tamil Nadu.
6. **Storm Independence:** Maximizing unique storm systems (covering 14 distinct cyclones across 18 granules).

---

## 2. Full 18-Granule Cohort Portfolio

```mermaid
pie title Gate D Cohort Distribution by Basin
    "Bay of Bengal (BoB)" : 11
    "Arabian Sea (AS)" : 7
```

| # | Cyclone Name | Season | Basin | Platform | MOSDAC gId | Nominal Acquisition (UTC) | IMD Wind (kt) | IMD Category | Strategic Role in Cohort |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **REMAL** *(Acquired)* | 2024 | BoB | INSAT-3DR | `13745265` | `2024-05-26 18:02` | 60.0 | SCS | Mature pre-landfall BoB anchor |
| **2** | **DANA** *(Acquired)* | 2024 | BoB | INSAT-3DS | `14514765` | `2024-10-25 23:30` | 20.0 | D (WML) | INSAT-3DS post-landfall weakening study |
| **3** | **AMPHAN** *(Acquired)*| 2020 | BoB | INSAT-3DR | `8353650` | `2020-05-19 23:58` | 95.0 | ESCS | Super cyclone peak intensity anchor |
| **4** | **BIPARJOY** *(Acquired)*| 2023 | AS | INSAT-3DR | `11789302` | `2023-06-12 23:58` | 85.0 | VSCS | Arabian Sea mature VSCS anchor |
| **5** | **TAUKTAE** *(Cand 01)* | 2021 | AS | INSAT-3DR | `9296007` | `2021-05-17 23:58` | 100.0 | ESCS | Arabian Sea extreme intensity benchmark |
| **6** | **FANI** *(Cand 02)* | 2019 | BoB | INSAT-3DR | `7206464` | `2019-05-02 23:58` | 115.0 | ESCS | Cat 4/5 equivalent BoB pre-landfall anchor |
| **7** | **MOCHA** *(Cand 03)* | 2023 | BoB | INSAT-3DR | `11621948` | `2023-05-13 23:58` | 115.0 | ESCS | Modern Cat 5 equivalent BoB super storm |
| **8** | **NISARGA** *(Cand 04)*| 2020 | AS | INSAT-3DR | `8410204` | `2020-06-03 23:58` | 60.0 | SCS | Eastern Arabian Sea Maharashtra impact |
| **9** | **ASNA** *(Cand 05)* | 2024 | AS | INSAT-3DS | `14089859` | `2024-08-30 23:30` | 40.0 | CS | Rare land-to-sea Arabian Sea storm (3DS) |
| **10**| **FENGAL** *(Cand 06)*| 2024 | BoB | INSAT-3DS | `14687507` | `2024-11-29 23:30` | 45.0 | CS | Modern Tamil Nadu coastal storm (3DS) |
| **11**| **YAAS** *(Cand 07)* | 2021 | BoB | INSAT-3DR | `9313313` | `2021-05-25 23:58` | 75.0 | VSCS | North BoB pre-landfall VSCS |
| **12**| **BULBUL** *(Cand 08)*| 2019 | BoB | INSAT-3DR | `7825908` | `2019-11-09 23:58` | 75.0 | VSCS | Late-season BoB recurving VSCS |
| **13**| **ASANI** *(Cand 09)* | 2022 | BoB | INSAT-3DR | `10179036` | `2022-05-09 23:54` | 55.0 | SCS | Recurving central BoB severe cyclonic storm |
| **14**| **MANDOUS** *(Cand 10)*| 2022 | BoB | INSAT-3DR | `10883728` | `2022-12-08 23:58` | 50.0 | SCS | Southwest BoB winter cyclonic storm |
| **15**| **MICHAUNG** *(Cand 11)*| 2023 | BoB | INSAT-3DR | `12726821` | `2023-12-04 23:58` | 55.0 | SCS | Heavy-rain slow-moving coastal cyclone |
| **16**| **TAUKTAE_EARLY** *(12)*| 2021 | AS | INSAT-3DR | `9276412` | `2021-05-15 23:58` | 55.0 | SCS | Rapid intensification phase in Arabian Sea |
| **17**| **MOCHA_EARLY** *(13)*| 2023 | BoB | INSAT-3DR | `11598234` | `2023-05-11 23:58` | 50.0 | SCS | Intensification phase of MOCHA in south BoB |
| **18**| **REMAL_DEV** *(14)* | 2024 | BoB | INSAT-3DR | `13734012` | `2024-05-25 06:00` | 25.0 | D | Cyclogenesis / initial depression stage |

---

## 3. Sampling Trade-Offs & Scientific Representation

1. **Statistical Representativeness vs Pilot Ceiling:**
   - 18 granules cannot constitute a fully asymptotic training set. However, by selecting 14 distinct storm systems rather than clustering 18 images across only 2 storms, we maximize the rank of the learned feature space.
2. **Multi-Stage vs Multi-Storm Trade-off:**
   - 11 of the 14 new candidates represent entirely distinct cyclones.
   - Only 3 candidates (`TAUKTAE_EARLY`, `MOCHA_EARLY`, `REMAL_DEV`) are second frames from existing storms, included deliberately to provide longitudinal intensification pairs for temporal feature evaluation.
3. **Arabian Sea Parity:**
   - Prior to Gate C Batch 1, the corpus had 0% Arabian Sea representation.
   - Following Gate D, Arabian Sea representation reaches **38.9%** (7 out of 18 granules), closely reflecting the historical climatological proportion of significant North Indian Ocean cyclones.

---

## 4. Execution Directives for Future Authorizations

- **Strict Sequential Batching:** Any future acquisition authorization must be executed in bounded batches of 2 to 3 granules (e.g. Batches D1 through D6 as detailed in `F2_4_GATE_D_ACQUISITION_PREFLIGHT.json`).
- **HTTP Range Resume Mandatory:** Every transfer must utilize Vayumarg's verified chunked range engine with automatic retry.
- **Strict Stop Directive:** This document provides planning blueprints only. **Zero bytes of new imagery are downloaded in Milestone F2.4 Gate C1R.**

