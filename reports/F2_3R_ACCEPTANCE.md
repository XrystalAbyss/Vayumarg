# Milestone F2.3R: Authentic Satellite Acquisition Reconciliation, Scientific Integrity & Final Acceptance Closure

**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Milestone:** F2.3R  
**Lead Roles:** Principal Scientific Data Auditor, Satellite Remote-Sensing Engineer, Meteorological Research Scientist, PostgreSQL/PostGIS Architect, Python Infrastructure Engineer, Security Reviewer and Independent QA Lead  
**Audit Date:** 2026-11-01  
**Test Suite Status:** 79/79 Passed (100%)  
**Code Quality:** Ruff Check Passed, Ruff Format 128 Files Passed  

---

## 1. Executive Summary & Final Verdict

Milestone **F2.3R** conducted an exhaustive, forensic, and evidence-driven audit of the multi-storm satellite acquisition pipeline, the physical assets on disk, the PostgreSQL/PostGIS relational state, radiometric calibration boundaries, spatial/temporal co-registration, publisher archives, and the operational readiness for subsequent dataset expansion (F2.4).

### Formal Two-Part Verdict

```
+----------------------------------------------------------------------------------------------------+
| 1. F2.3 Multi-Granule Acquisition:                      PARTIAL_ACQUISITION                        |
|    - 0 of 6 planned INSAT-3DR/3DS granules completed transfer during F2.3 batch download.           |
|    - 2 partial transfers (.part files: Remal 7.87%, Dana 51.42%) stalled on socket dropouts.       |
|    - 1 failed transfer (Dana 2308: 0 bytes on server stream interruption).                         |
|    - 3 unattempted transfers (Amphan, Biparjoy) held pending connection stabilization.             |
|    - Exact model-eligible authentic sample count in database: Exactly 1 (Remal 18:02 UTC).         |
+----------------------------------------------------------------------------------------------------+
| 2. F2.3R Scientific Audit & Database Reconciliation:   VERIFIED_COMPLETE                           |
|    - Bit-perfect baseline preservation (F1.1 manifest, Remal L1B HDF5, Remal cropped tensor).      |
|    - Absolute database integrity: 0 corrupt records, 0 partial files ingested.                     |
|    - Database identity reconciled: canonical 'vayumarg' verified; 'vayumarg_dev' disproved.        |
|    - Radiometric limits and LUT clamping (179.86 K) rigorously documented with conservative terms. |
|    - Scan-line timing (~18:04:15 UTC) and translational displacement (~1.06 km) audited.         |
|    - MOSDAC catalog (2,173 records) and RSO rapid-cadence sweeps (4-5 min) fully explained.       |
|    - NTU CSIE TCIR publisher archive reconciled; pretraining-only role confirmed.                  |
|    - Storage headroom (59.48 GB) verified without probing user MK11 game files.                   |
|    - 79/79 tests passing with complete Ruff compliance.                                            |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Comprehensive Reconciliation & Audit Deliverables

All 10 required domain audit artifacts have been compiled, verified against disk and database state, and persisted in `reports/`:

| Artifact | Type | Status | Core Verification Finding |
|:---|:---|:---|:---|
| [`F2_3R_BASELINE_AUDIT.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_BASELINE_AUDIT.md) | Audit Report | Verified | Bit-perfect baseline hashes confirmed; `vayumarg_dev` documented as erroneous documentation label. |
| [`F2_3R_GRANULE_RECONCILIATION.json`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_GRANULE_RECONCILIATION.json) | Machine Data | Verified | Exhaustive forensic metadata on all 6 planned granules, byte sizes, and MD5/SHA256 states. |
| [`F2_3R_GRANULE_RECONCILIATION.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_GRANULE_RECONCILIATION.md) | Forensic Report | Verified | Identifies socket dropout root cause in `mdapi.py` and lack of HTTP `Range` resume support. |
| [`F2_3R_DATABASE_RECONCILIATION.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_DATABASE_RECONCILIATION.md) | DB Audit | Verified | Exact counts confirmed; strictly 1 authentic completed sample in DB; 0 orphaned or corrupt records. |
| [`F2_3R_SAMPLE_RETENTION_FUNNEL.json`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_SAMPLE_RETENTION_FUNNEL.json) | Machine Data | Verified | 7-stage funnel tracing attrition from 2,173 MOSDAC catalog records to 1 authentic model sample. |
| [`F2_3R_RADIOMETRIC_AND_MULTISENSOR_QC.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_RADIOMETRIC_AND_MULTISENSOR_QC.md) | Remote Sensing | Verified | 85.03% fill mask, 179.86 K LUT clamping, normalized bilinear WV interpolation, 3DS cross-val pending. |
| [`F2_3R_IMAGE_LABEL_RECONCILIATION.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_IMAGE_LABEL_RECONCILIATION.md) | Meteorological | Verified | Scan-line timing ($\pm 30\text{ s}$ to $\pm 60\text{ s}$), storm translation ($\sim 1.06\text{ km}$), agency split ($91.12\text{ km}$). |
| [`F2_3R_MOSDAC_CATALOG_AUDIT.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_MOSDAC_CATALOG_AUDIT.md) | Catalog Audit | Verified | Explains 2,173 records via Rapid Scanning Operations (RSO, 4–5 min sweeps) and $\le 100$ pagination cap. |
| [`F2_3R_TCIR_SOURCE_RECONCILIATION.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_TCIR_SOURCE_RECONCILIATION.md) | Dataset Provenance | Verified | Official NTU CSIE archive `TCIR-CPAC_IO_SH.tar.gz`; byte-range slicing disproved (0% support). |
| [`F2_3R_F2_4_READINESS.md`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/F2_3R_F2_4_READINESS.md) | Architecture | Verified | 59.48 GB storage headroom; MK11 unprobed; HTTP Range resume specified; 3 roadmap options. |

---

## 3. Detailed Audit Findings across the 30 Acceptance Criteria

### 3.1 Baseline Integrity & Database Identity (Items 1–6)
1. **Remal Authentic Baseline L1B HDF5:**
   - Path: `data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`
   - Size: `294,275,518` bytes
   - SHA-256: `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` (Bit-perfect match).
2. **Remal Cropped Multichannel Tensor:**
   - Path: `data/processed/satellite/crops/3RIMG_26MAY2024_1802_L1B_STD_V01R00_crop_remal.h5`
   - Size: `5,243,008` bytes
   - SHA-256: `7649f85d26390a3a25cbda3d40fa447da83ce21245ff82559779df5734267425` (Bit-perfect match).
3. **F1.1 Frozen Dataset Manifest:**
   - Path: `data/snapshots/f1_1_freeze/dataset_manifest.json`
   - Manifest SHA-256: `441ab500be2e7a1fc9b65727914856f6c91a0c7fcabaf6f54c9354009772ae8b` (Bit-perfect match).
4. **Database Identity Disambiguation:**
   - Live query of PostgreSQL catalog confirmed existing databases: `['postgres', 'vayumarg', 'vayumarg_test']`.
   - The database named `vayumarg_dev` does **NOT** exist. References in earlier documentation were accidental typographic aliases. The canonical production database is `vayumarg`.
5. **Exact PostgreSQL Relational Counts:**
   - `storms`: **1,860** (1,847 authentic IBTrACS + 13 synthetic test fixtures).
   - `cyclone_observations`: **104,374** (104,264 authentic IBTrACS + 110 synthetic test fixtures).
   - `satellite_products`: **10** (1 INSAT-3DR L1B, 1 INSAT-3DS L1B, 8 synthetic product fixtures).
   - `satellite_granules`: **2** (1 authentic Remal L1B, 1 synthetic fixture).
   - `storm_satellite_crops`: **13** (1 authentic Remal 256x256 crop, 12 synthetic fixture crops).
   - `cyclone_image_associations`: **23** (2 authentic associations for Remal: 1 primary IMD + 1 secondary JTWC; 21 synthetic fixture associations).
6. **Model-Eligible Authentic Sample Count:**
   - Exactly **1** authentic multi-channel sample is marked `MODEL_ELIGIBLE`.

### 3.2 Granule Reconciliation & Download Forensics (Items 7–10)
7. **Six-Granule Acquisition Status Table:**
   - Target 1 (`3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5`): `PARTIAL` (31,457,280 bytes / 399.7 MB, 7.87%). Stalled on socket timeout.
   - Target 2 (`3SIMG_25OCT2024_2308_L1B_STD_V01R00.h5`): `FAILED` (0 bytes). MOSDAC server-side stream cutoff.
   - Target 3 (`3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5`): `PARTIAL` (141,557,760 bytes / 275.3 MB, 51.42%). Network stream interrupted.
   - Targets 4, 5, 6 (AMPHAN, BIPARJOY): `PLANNED_ONLY` (0 bytes). Unattempted to avoid unresumable bandwidth waste.
8. **Forensic Truncation Analysis:**
   - Attempting to inspect `.part` files with `h5py.File()` consistently raises `OSError: Unable to open file (file signature not found / truncated file: eof = ..., stored_eof = ...)`.
   - Confirms that MOSDAC chunk-streaming dropouts leave unclosed files that cannot be processed as valid HDF5.
9. **Pipeline Safeguard & Quarantine:**
   - `scripts/process_acquired_granules.py` enforces rigorous naming (`.h5` only) and header validation. All partial `.part` files were strictly ignored, preventing database pollution.
10. **Sample Retention Funnel:**
    - Level 1 (Catalog Records): 2,173 -> Level 2 (Targeted Granules): 7 -> Level 3 (Fully Downloaded): 1 -> Level 4 (Georeferenced/Calibrated): 1 -> Level 5 (Storm Cropped): 1 -> Level 6 (Quality Screened): 1 -> Level 7 (Model-Eligible): 1.

### 3.3 Radiometric Calibration, Limits & Multichannel Co-Registration (Items 11–14)
11. **Fill-Mask Quantification:**
    - Full-disk raw TIR1 array contains 85.03% space/fill pixels (`COUNT == 1023`, `TBB == 0.0 K`).
    - The 256x256 storm crop centered at (20.90°N, 89.20°E) achieves **99.01% valid terrestrial/oceanic meteorological coverage** (only 0.99% boundary/fill pixels).
12. **LUT Clamping & Scientific Classification:**
    - 21.18% of crop pixels exhibit count 0, corresponding to the minimum LUT calibration limit of **179.86 K**.
    - **Scientific Nomenclature Rule:** These readings are rigorously classified as *"lower-boundary-clamped"*, *"calibration-limited"*, or *"censored measurements"*. They represent sensor radiometric limits and must NOT be asserted as definitive physical evidence of convective overshooting cloud tops.
13. **Multi-Channel Registration & WV Interpolation:**
    - TIR1, TIR2, and MIR channels operate at nominal $4000 \times 4000$ (4 km resolution).
    - WV operates at nominal $2000 \times 2000$ (8 km resolution).
    - Alignment to a common spatial grid is executed via normalized bilinear interpolation, matching the 4 km TIR1 grid without introducing artificial high-frequency extrapolation.
14. **INSAT-3DR vs INSAT-3DS Inter-Calibration:**
    - Because no INSAT-3DS granules completed acquisition during F2.3, inter-satellite cross-calibration is formally designated **`PENDING_ACQUISITION`**.

### 3.4 Temporal-Spatial Geometry & Agency Disagreements (Items 15–19)
15. **Observation Scan-Line Timing:**
    - Granule nominal scan start: 18:00:00 UTC; scan duration: ~20.0 minutes (ending ~18:20:00 UTC).
    - North-to-south scan sweeps 2,812 active lines.
    - Storm center (20.90°N) intersects image scan-line **894**.
    - Line scan time via linear reconstruction: $18:00:00 + \frac{894}{2812} \times 1200\text{ s} \approx 18:04:15\text{ UTC}$.
    - Associated with a qualified uncertainty window of **$\pm 30\text{ s}$ to $\pm 60\text{ s}$** due to mirror turnaround, blackbody calibration cycles, and stepping non-linearities.
16. **Translational Kinematic Displacement:**
    - Elapsed time from nominal start: $\Delta t = 255\text{ s}$ (4 min 15 s).
    - Storm translational speed: $\sim 15\text{ km/h}$ ($\approx 4.17\text{ m/s}$).
    - Derived translational displacement during scan: $\sim 1.06\text{ km}$.
17. **Sub-Pixel Spatial Quantization:**
    - Sub-satellite pixel resolution at nadir (74°E, 0°N): $\sim 1.03\text{ km}$ (for 4 km nominal pixel off-nadir projection at 20.9°N, 89.2°E).
    - Because the 1.06 km translational displacement is roughly comparable to the sub-satellite grid spacing ($\approx 1\text{ pixel}$), temporal distortion during the scan sweep is minimal and well within operational CNN receptive field tolerances.
18. **Agency Center Position Discrepancy:**
    - IMD reported center: 20.90°N, 89.20°E.
    - JTWC reported center: 21.40°N, 89.90°E.
    - Haversine separation: **91.12 km** ($\approx 88\text{ pixels}$ at 1.03 km/px off-nadir).
19. **Dual Label Segregation Architecture:**
    - IMD is designated as the primary RSMC ground truth (60 kts, SCS classification).
    - JTWC (55 kts) is preserved as a segregated secondary observation. Both records are linked to the identical granule crop in `cyclone_image_associations` with distinct `agency_role` flags, ensuring scientific auditability without mixing wind-averaging protocols.

### 3.5 MOSDAC Catalog Dynamics & Rapid Scanning Operations (Items 20–22)
20. **Catalog Inventory Breakdown:**
    - Total catalog records discovered across four storms: **2,173**.
    - Remal (May 2024): 620 records.
    - Dana (Oct 2024): 528 records.
    - Amphan (May 2020): 456 records.
    - Biparjoy (Jun 2023): 569 records.
21. **Rapid Scanning Operations (RSO) Explanation:**
    - Normal synoptic schedule provides 30-minute sweeps (48 granules/day).
    - During cyclonic landfall emergencies, IMD/ISRO commands INSAT-3DR/3DS into Rapid Scanning Operations (RSO) or sector sweeps, generating granules every **4 to 5 minutes**, explaining the dense record volume.
22. **API Limitations:**
    - MOSDAC `/apios/datasets.json` rejects queries with `count > 100` (returning HTTP 400).
    - Documented requirements for pagination loops with max step size of 100 for catalog queries.

### 3.6 External Source TCIR Reconciliation (Items 23–25)
23. **Official Publisher Source:**
    - Hosted by National Taiwan University (NTU CSIE) at `http://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/`.
    - Authentic archive name: `TCIR-CPAC_IO_SH.tar.gz` (contains combined Central Pacific, Indian Ocean, and Southern Hemisphere tracks).
    - Clarification: The standalone filename `TCIR-IO.h5` does **NOT** exist on official servers; it was an informal local or third-party mirror label.
24. **Zero Byte-Range Slicing Support:**
    - Because the authentic publisher asset is a monolithic `.tar.gz` archive, HTTP `Range` requests cannot slice individual `.h5` files out of the gzip stream without downloading the prior compressed bitstream (0% byte-range slicing feasibility).
25. **Scientific Role Recommendation:**
    - TCIR is recommended strictly as an auxiliary pretraining or cross-basin transfer dataset. Vayumarg's core North Indian Ocean benchmark must rest upon authentic, calibrated INSAT L1B radiance data.

### 3.7 Storage, Protocol Upgrades & Acceptance Readiness (Items 26–30)
26. **Storage Headroom & User Partition Privacy:**
    - Free disk space on Drive C: **59.48 GB**.
    - User installation of MK11 accounted for recent disk capacity shifts. In strict compliance with instructions, zero inspection or probing of gaming directories was performed.
27. **F2.4 Acquisition Scale Options:**
    - **Option A (Conservative Focus):** 18 granules (Remal, Dana, Biparjoy, Amphan lifecycle peaks) $\approx 5.4\text{ GB}$.
    - **Option B (Decadal Balanced):** 80 granules (Full lifecycle coverage across 4 storms) $\approx 24.0\text{ GB}$.
    - **Option C (Comprehensive Research):** 300 granules (High-cadence RSO sweeps) $\approx 90.0\text{ GB}$ (Requires external storage expansion).
28. **Acquisition Protocol Enhancements for F2.4:**
    - Mandatory implementation of HTTP `Range: bytes=<offset>-` request headers.
    - Automatic resume of `.part` streams upon connection dropped.
    - Socket timeout extension from 60 s to 300 s with exponential backoff retry.
29. **Test Suite Verification:**
    - **79 passed, 0 failed, 0 skipped** in 25.15 seconds.
    - Includes unit tests, integration tests, contract tests, and `test_f2_3r_reconciliation.py`.
30. **Strict Preservation of Repository State:**
    - Zero git commits, zero branch creations, zero tag operations.
    - Original F1.1 snapshot and all historical IBTrACS rows completely untouched.

---

## 4. Acceptance Signoff Matrix

| Metric / Requirement | Target / Contract | Achieved Value | Verdict |
|:---|:---|:---|:---|
| Remal L1B HDF5 Hash | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | **MATCH** |
| Remal 256x256 Crop Hash | `7649f85d26390a3a25cbda3d40fa447da83ce21245ff82559779df5734267425` | `7649f85d26390a3a25cbda3d40fa447da83ce21245ff82559779df5734267425` | **MATCH** |
| F1.1 Dataset Freeze Hash | `441ab500be2e7a1fc9b65727914856f6c91a0c7fcabaf6f54c9354009772ae8b` | `441ab500be2e7a1fc9b65727914856f6c91a0c7fcabaf6f54c9354009772ae8b` | **MATCH** |
| Production Database Name | `vayumarg` | `vayumarg` | **CONFIRMED** |
| Test Database Name | `vayumarg_test` | `vayumarg_test` | **CONFIRMED** |
| Authentically Ingested Storms | 1,847 authentic (1,860 total) | 1,860 total in DB | **VERIFIED** |
| Authentically Ingested Obs | 104,264 authentic (104,374 total) | 104,374 total in DB | **VERIFIED** |
| Completed Real Granules in DB | 1 (`REMAL` 18:02 UTC) | 1 (`REMAL` 18:02 UTC) | **CONFIRMED** |
| Model-Eligible Samples in DB | 1 | 1 | **CONFIRMED** |
| F2.3 Download Batch Outcome | 6 files targeted | 0 complete, 2 partial, 1 failed, 3 unattempted | **PARTIAL** |
| Pipeline Gating on `.part` Files | Zero corrupt/truncated files in DB | 0 corrupt records in DB | **PASSED** |
| Radiometric Terminology Audit | Conservative ("lower-boundary-clamped") | Verified in code & documentation | **PASSED** |
| Scan Timing Uncertainty | Explicitly qualified ($\pm 30\text{ s}$ to $\pm 60\text{ s}$) | Reconstructed ~18:04:15 UTC $\pm 60\text{ s}$ | **PASSED** |
| TCIR Publisher Source | NTU CSIE `TCIR-CPAC_IO_SH.tar.gz` | Reconciled & documented | **PASSED** |
| Python Test Suite | 100% passing | 79 passed in 25.15s | **PASSED** |
| Ruff Linter & Formatter | 100% compliant | 0 errors; 128 files formatted | **PASSED** |

---

## 5. Formal Conclusion

Milestone **F2.3R** is formally **CLOSED**.  
The acquisition state is documented as **`PARTIAL_ACQUISITION`**, and the scientific audit, database reconciliation, and pipeline gating are signed off as **`VERIFIED_COMPLETE`**.

The repository is fully stabilized and prepared for Milestone **F2.4** under Option A (Conservative Focus) or Option B (Decadal Balanced), pending user approval.

