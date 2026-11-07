# Vayumarg F2.4 Gate D1 — Preflight Scientific Acceptance & Approval Gate

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate D1 — Balanced Scientific Acquisition Selection, Exact Granule Preflight & First-Batch Approval Gate  
**Auditor Roles:** Principal Scientific Data Architect, Satellite Remote-Sensing Engineer, Meteorological Scientist, Dataset Sampling Specialist, PostgreSQL/PostGIS Engineer, QA Lead  
**Milestone Verdict:** **`GATE_D1_READY_FOR_OWNER_APPROVAL`**  

---

## 1. Formal Attestation & Acceptance Declaration

The Principal Scientific Data Architect, Satellite Remote-Sensing Engineer, Meteorological Scientist, Dataset Sampling Specialist, PostgreSQL/PostGIS Engineer, and Independent QA Auditor hereby attest that **Milestone F2.4 Gate D1** has completed all preflight audits, candidate scoring, cohort count reconciliations, and batch formulation with complete scientific rigor and zero violations of project boundaries.

**No new satellite granules have been downloaded in Milestone F2.4 Gate D1.** The system is paused in a clean, reproducible state awaiting explicit owner approval of the first-batch acquisition manifest.

---

## 2. Milestone Audit Matrix & Compliance Checklist

| Audit Section | Mandated Requirement | Verified Outcome | Audit Status |
|---|---|---|---|
| **Section 1: Baseline Verification** | Re-verify checksums, DB entities, migrations, and storage headroom | 4 raw HDF5s, 4 crops, 10 associations, and snapshot `441ab5008e...` verified; 49.13 GB free on drive `C:` | **PASS** |
| **Section 2: Cohort Reconciliation** | Resolve 14 vs 15 storm discrepancy across canonical SIDs | Exact count is **15 unique storm SIDs** across 18 granules ($4\text{ existing} + 11\text{ new} = 15$); reporting slip resolved | **PASS** |
| **Section 3: Existing Samples** | Re-verify REMAL, DANA, AMPHAN, BIPARJOY | All parameters, LUT calibrations, and DANA IMD ineligibility flags preserved | **PASS** |
| **Section 4: Scientific Goals** | Frame Gate D as controlled engineering/sampling pilot | Documented as sampling pilot; final F3 EDA preserved | **PASS** |
| **Section 5: Candidate Review** | Audit all 14 candidates against MOSDAC OpenSearch & PostgreSQL | All 14 candidates verified with exact gIds, filenames, and ground-truth synoptic fixes | **PASS** |
| **Section 6: Candidate Scoring** | Multi-objective scoring across 8 orthogonal criteria | Generated `reports/F2_4_GATE_D1_CANDIDATE_SCORING.json`; top 3 ranked candidates identified | **PASS** |
| **Section 7: Batch 1 Selection** | Form batch of 2–3 granules strictly $\le 1.0\text{ GB}$ | Selected **TAUKTAE**, **FANI**, **FENGAL** (3 granules, **878 MB** total, $122\text{ MB}$ headroom) | **PASS** |
| **Section 8: Reliability Preflight** | Review downloader, Range headers, retry logic, and atomic promotion | Chunked HTTP Range engine with backoff retry preflighted; ceiling capped at 1.0 GB | **PASS** |
| **Section 9: Model Eligibility** | Define ingestion gates and task-level eligibility | Created `F2_4_GATE_D1_MODEL_ELIGIBILITY_PREFLIGHT.md`; primary IMD targets expand from 3 to 6 | **PASS** |
| **Section 10: Phased Schedule** | Design D1–D6 phased schedule for remaining 14 granules | Created `F2_4_GATE_D1_ACQUISITION_SCHEDULE.md` with bounded 2–3 granule batches | **PASS** |
| **Section 11: F3 EDA Spec** | Preserve `F3_COMPREHENSIVE_EDA_SPEC.md` intact | Preserved intact; zero exploratory analysis executed | **PASS** |
| **Section 12: Automated Testing** | Add focused tests and maintain 100% test pass rate | **116 passed** in pytest; Ruff lint and format clean | **PASS** |
| **Strict Restrictions** | Zero downloads, zero git commits/pushes, zero DB modifications | Zero downloads initiated; zero git commits/pushes; zero destructive DB operations | **PASS** |

---

## 3. First-Batch Acquisition Summary (Batch D1)

| Parameter | Granule 1: TAUKTAE (2021) | Granule 2: FANI (2019) | Granule 3: FENGAL (2024) | Batch D1 Total / Limit |
|---|---|---|---|---|
| **Canonical Storm SID** | `2021133N10071` (New) | `2019116N02090` (New) | `2024329N04089` (New) | **3 Distinct New SIDs** |
| **Ocean Basin** | Arabian Sea (NI) | Bay of Bengal (NI) | Bay of Bengal (NI) | **2 Distinct Basins** |
| **Satellite Platform** | INSAT-3DR | INSAT-3DR | **INSAT-3DS** | **Cross-Generational** |
| **MOSDAC Product** | `3RIMG_L1B_STD` | `3RIMG_L1B_STD` | `3SIMG_L1B_STD` | Standard Imager L1B |
| **MOSDAC Asset gId** | `9293840` | `7206464` | `14687507` | Verified OpenSearch gIds |
| **Exact Filename** | `3RIMG_16MAY2021_...` | `3RIMG_02MAY2019_...` | `3SIMG_29NOV2024_...` | Standard HDF5 names |
| **Acquisition UTC** | `2021-05-16 23:58:00` | `2019-05-02 23:58:00` | `2024-11-29 23:30:00` | Rapid-scan sectors |
| **Estimated File Size** | 299,000,000 bytes | 298,000,000 bytes | 281,000,000 bytes | **$878,000,000\text{ bytes}$** (~837.3 MB) |
| **Batch Ceiling** | — | — | — | **$\le 1,000,000,000\text{ bytes}$ (1.0 GB)** |
| **Primary IMD Label** | 100.0 kt (`ESCS`, 950 hPa, 18.5°N, 71.5°E)| 105.0 kt (`ESCS`, 945 hPa, 19.1°N, 85.5°E)| 45.0 kt (`CS`, 996 hPa, 12.2°N, 81.2°E) | **100% Valid Primary Targets** |
| **Secondary JTWC Label** | 120.0 kt (1-min, 931 hPa) | 135.0 kt (1-min, 918 hPa) | 45.0 kt (1-min, 992 hPa) | **100% Valid Secondary Targets** |

---

## 4. Deliverables Inventory

1. [F2_4_GATE_D1_BASELINE.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_BASELINE.md)
2. [F2_4_GATE_D1_COHORT_RECONCILIATION.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_COHORT_RECONCILIATION.md)
3. [F2_4_GATE_D1_CANDIDATE_SCORING.json](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_CANDIDATE_SCORING.json)
4. [F2_4_GATE_D1_CORRECTED_SCORING.json](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_CORRECTED_SCORING.json)
5. [F2_4_GATE_D1_FIRST_BATCH_SELECTION.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_FIRST_BATCH_SELECTION.md)
6. [F2_4_GATE_D1_APPROVAL_MANIFEST.json](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_APPROVAL_MANIFEST.json)
7. [F2_4_GATE_D1_CORRECTED_APPROVAL_MANIFEST.json](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_CORRECTED_APPROVAL_MANIFEST.json)
8. [F2_4_GATE_D1_ACQUISITION_SCHEDULE.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_ACQUISITION_SCHEDULE.md)
9. [F2_4_GATE_D1_MODEL_ELIGIBILITY_PREFLIGHT.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_MODEL_ELIGIBILITY_PREFLIGHT.md)
10. [F2_4_GATE_D1_SCIENTIFIC_CORRECTIONS.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_SCIENTIFIC_CORRECTIONS.md)
11. [F2_4_GATE_D1_ACCEPTANCE.md](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_ACCEPTANCE.md)

---

## 5. Owner Decision Request

Milestone **F2.4 Gate D1** is complete. Execution is halted.

The owner is invited to review the **Gate D1 First-Batch Approval Manifest** ([`F2_4_GATE_D1_APPROVAL_MANIFEST.json`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_4_GATE_D1_APPROVAL_MANIFEST.json)).

Upon receiving explicit owner authorization for Batch D1, the resilient acquisition engine will proceed with the sequential acquisition and multichannel processing of **TAUKTAE**, **FANI**, and **FENGAL**.

