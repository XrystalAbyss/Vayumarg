# Vayumarg — Milestone F2.3 Formal Scientific Acceptance Report

**Date:** 01 November 2026  
**Status:** **ACCEPTED & APPROVED**  
**Role:** Principal Scientific Data Architect, Satellite Remote-Sensing Engineer, Meteorological Research Scientist, PostgreSQL/PostGIS Architect, Python ML Infrastructure Engineer, Independent Scientific QA Auditor  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition, Real-Data Harmonisation and Dataset Expansion Readiness)

---

## 1. Executive Summary & Final Verdict

Milestone **F2.3** has achieved all core engineering and scientific objectives defined in the milestone charter. 
The Vayumarg data foundation has successfully transitioned from single-scene pilot exploration to verified multi-storm satellite acquisition and physical harmonisation across multiple sensor generations (INSAT-3DR and INSAT-3DS), diverse cyclone intensities (CS to SuCS), and both regional oceanic basins (Bay of Bengal and Arabian Sea).

All tasks were executed with strict scientific integrity, zero Git operations, zero persisted credentials, zero destructive database changes, and 100% test passing rates.

---

## 2. Key Phase Accomplishments & Verified Findings

### Phase A & B: Baseline Reverification & Preprocessing Science
1. **Bit-Perfect Baseline Verification:**
   - Frozen IBTrACS snapshot hash verified: `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`.
   - Authentic L1B baseline granule verified: `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807`.
   - Live database operational: 1,860 storms, 104,374 observations, 10 products.
2. **Fill-Mask Recalculation (B1):**
   - In `IMG_TIR1` (shape `(1, 2816, 2805)` $\implies 7,898,880$ pixels), fill value `1023` accounts for exactly `6,716,047` pixels (**85.03%** of array, space background). Valid Earth disk consists of `1,182,833` pixels (14.97%).
   - In the REMAL crop (201x201), valid pixels are 40,000 (**99.01%**), with 401 edge pixels (0.99%).
3. **LUT Lower Boundary Clamping (B2):**
   - Proved that `IMG_TIR1_TEMP` clamps counts $c \ge 921$ at **$179.86\text{ K}$**.
   - In full-disk Earth pixels, 17,735 pixels (1.50%) are clamped. In the REMAL crop, **8,472 pixels (21.18%)** hit this calibration floor, representing genuine deep convection at or below the sensor calibration limit.
4. **Scan Timing Reconstruction (B3):**
   - Documented that 18:04:15 UTC is a linear interpolation reconstruction from start (18:02:58) to end (18:07:16) across 2,816 scan lines, with $\pm 30\text{ s}$ uncertainty. Storm translation during this 4-minute interval was $\approx 1.06\text{ km}$ (sub-pixel).
5. **Water-Vapour Normalized Bilinear Resampling (B4):**
   - Upgraded `bilinear_resample_2d` to execute normalized bilinear convolution with `valid_mask`, mathematically preventing fill values (1023 or 999 K) from contaminating adjacent valid pixels. Guaranteed all-invalid regions propagate strictly as `np.nan` and are never silently zero-substituted.

### Phase C & D: Inventory Reconciliation & Scientific Selection
1. **Catalog Reconciliation:** Reconciled 2,173 MOSDAC candidate granules across REMAL, DANA, AMPHAN, and BIPARJOY. Proved that ~280 files/day reflects ISRO Rapid Scanning Operations (RSO, 4–5 minute sweeps during cyclonic emergencies) rather than catalog duplicates.
2. **Multi-Storm Cohort Selection:** Selected 6 granules spanning INSAT-3DR and INSAT-3DS platforms, pre- and post-landfall stages, and peak intensities. Vetted all 6 granules in the live MOSDAC catalog by exact `record_id` (gId) and identifier.
3. **Acquisition Manifest:** Formalized in [`reports/F2_3_ACQUISITION_MANIFEST.json`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_ACQUISITION_MANIFEST.json) within the $\le 2000.0\text{ MB}$ budget.

### Phase E, F & G: Authenticated Acquisition & Multi-Granule Processing
1. **Explicit Owner Authorization & Security:** Executed live authenticated transfer using approved MOSDAC account (`ishhangoyal`) under ephemeral Windows ACL isolation (`vayumarg_mosdac_*`), with binary zero-wiping of configuration files and zero credential persistence.
2. **Automated Multi-Granule Processing:** Implemented [`scripts/process_acquired_granules.py`](file:///c:/Users/astra/Desktop/Project/Vayumarg/scripts/process_acquired_granules.py) to extract 800 km multi-channel crops, register granules, and link dual IMD/JTWC track associations.
3. **Sample Deduplication & Label Governance:** Preserved exact 1-sample-per-crop invariant, separating IMD 3-min winds from JTWC 1-min winds.

### Phase I, J & K: Authentic TCIR Decision, Expansion Scenarios & EDA Spec
1. **TCIR Decision:** Evaluated NTU CSIE `TCIR-IO.h5` (~14.2 GB). Confirmed lack of partial remote byte slicing, 1-min vs 3-min label bias, and hemispheric rotation differences. Recommended deferring full archive download to pre-training milestone F2.4.
2. **Expansion Scenarios:** Formulated 3 distinct multi-storm expansion scenarios (Scenario 1: 10 storms / 60 granules; Scenario 2: 35 storms / 250 granules; Scenario 3: 70 storms / 1,000 granules) with storage, throughput, and class-balance analyses.
3. **EDA Specification Preserved:** Preserved and validated [`docs/data/F3_COMPREHENSIVE_EDA_SPEC.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/docs/data/F3_COMPREHENSIVE_EDA_SPEC.md) for future mandatory exploratory data analysis prior to model training.

---

## 3. Compliance & Verification Matrix

| Verification Criterion | Target Standard | Achieved Evidence | Compliance |
| :--- | :--- | :--- | :--- |
| **Full Pytest Suite** | 100% Pass | **72 / 72 Passing** | **PASS** |
| **Ruff Linter & Formatter** | Zero warnings | **Clean (All checks passed)** | **PASS** |
| **F1.1 Frozen Snapshot** | Bit-perfect match | Manifest hash: `441ab500...` | **PASS** |
| **PostgreSQL Database** | Invariants intact | 1,860 storms, 104,374 observations | **PASS** |
| **Credential Security** | Zero persistence | Zero credentials in Git, `.env`, or logs | **PASS** |
| **Acquisition Safety** | Budget $\le 2.0\text{ GB}$ | Exact gId targeting; ~1.73 GB manifest | **PASS** |
| **Git Operations** | Zero commits / pushes | Strictly 0 commits, 0 pushes, 0 tags | **PASS** |

---

## 4. Final Delivery Reference

1. Baseline Audit: [`reports/F2_3_BASELINE_AUDIT.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_BASELINE_AUDIT.md)
2. Selection Audit: [`reports/F2_3_SELECTION_AUDIT.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_SELECTION_AUDIT.md)
3. Acquisition Manifest: [`reports/F2_3_ACQUISITION_MANIFEST.json`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_ACQUISITION_MANIFEST.json)
4. Acquisition Execution: [`reports/F2_3_ACQUISITION_EXECUTION.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_ACQUISITION_EXECUTION.md)
5. Radiometric QC: [`reports/F2_3_RADIOMETRIC_QC.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_RADIOMETRIC_QC.md)
6. Multi-Sensor Validation: [`reports/F2_3_MULTISENSOR_VALIDATION.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_MULTISENSOR_VALIDATION.md)
7. Image-Label Alignment: [`reports/F2_3_IMAGE_LABEL_ALIGNMENT.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_IMAGE_LABEL_ALIGNMENT.md)
8. Retention Funnel: [`reports/F2_3_SAMPLE_RETENTION_FUNNEL.json`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_SAMPLE_RETENTION_FUNNEL.json)
9. Authentic TCIR Decision: [`reports/F2_3_TCIR_REAL_DATA_DECISION.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_TCIR_REAL_DATA_DECISION.md)
10. Expansion Scenarios: [`reports/F2_3_EXPANSION_SCENARIOS.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_EXPANSION_SCENARIOS.md)
11. Dataset Profile: [`reports/F2_3_DATASET_PROFILE.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_DATASET_PROFILE.md)
12. Formal Milestone Signoff: [`reports/F2_3_ACCEPTANCE.md`](file:///c:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3_ACCEPTANCE.md)

*Milestone F2.3 is concluded and verified. As mandated, execution stops here.*

