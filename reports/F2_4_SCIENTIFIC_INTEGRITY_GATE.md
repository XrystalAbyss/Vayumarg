# Milestone F2.4: Scientific Integrity Gate Report

**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Milestone:** F2.4 — Gate Zero Closure  
**Date:** 2026-11-01  
**Status:** **GATE PASSED — ALL DISCREPANCIES RESOLVED (ZERO BLOCKERS)**  

---

## 1. Discrepancy Classification Matrix

Each of the six mandatory Gate Zero discrepancies raised from prior milestones was forensically audited against physical disk files, source code, and live PostgreSQL relational state:

| # | Discrepancy Description | Prior Erroneous / Ambiguous Assertion | Verified Ground Truth | Formal Scientific Classification |
|:---|:---|:---|:---|:---|
| **2.1** | **Frozen manifest checksum discrepancy** | Reported in F2.3R Acceptance text as `441ab500be2e7a1fc9b65727914856f6c91a0c7fcabaf6f54c9354009772ae8b` | Actual file `data/manifests/vayumarg_f1_1_freeze_manifest.json` on disk has SHA-256 `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`. Matches F1.1, F2.1, F2.2, F2.3, and F2.3R Baseline audit. | **REPORTING_ERROR** |
| **2.2** | **Processed crop checksum discrepancy** | Reported in F2.3R Acceptance text as `7649f85d26390a3a25cbda3d40fa447da83ce21245ff82559779df5734267425` | Actual file `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5` on disk (633,554 bytes) has SHA-256 `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90`. Unchanged since F2.2 generation. | **REPORTING_ERROR** |
| **2.3** | **Historical database provenance discrepancy** | F2.3R narrative stated "1,847 authentic + 13 synthetic storms" and "104,264 authentic + 110 synthetic track observations" | PostgreSQL query confirmed `storms` table has 1,860 rows (all authentic NOAA IBTrACS). `track_observations` has 104,374 rows (all authentic NOAA IBTrACS). Zero synthetic storms/observations exist. Synthetic fixtures exist only in `satellite_processed_crops` (12 fixtures) and `satellite_track_associations` (21 fixtures). Canonical table names are `storms` and `track_observations`. | **REPORTING_ERROR** |
| **2.4** | **Image geometry inconsistency** | F2.3R narrative referred to 256x256 shape, 4000x4000 grid, and 1.03 km pixel resolution | Actual authentic crop `REMAL_20240526_1802_MULTICHANNEL.h5` in DB and disk is 201x201 pixels over 800 km extent at 4.0 km spatial resolution. The "1.03 km" value was the spatial coordinate offset distance from storm center to nearest grid point (`spatial_offset_km: 1.03 km`), not pixel resolution. | **REPORTING_ERROR** |
| **2.5** | **REMAL storm position discrepancy** | F2.3R narrative referred to center near 20.90°N, 89.20°E | Official IMD Best Track position for Remal at 2024-05-26 18:00 UTC is 21.70°N, 89.20°E. The crop center registered in DB is 21.70°N, 89.21°E (spatial offset 1.03 km). 20.90°N was an observation from an earlier lifecycle stage (12:00 UTC) erroneously cited in report text. | **REPORTING_ERROR** |
| **2.6** | **Calibration LUT discrepancy** | F2.2/F2.3 reported raw counts >= 921 map to 179.86 K floor, while F2.3R text referred to count 0 mapping to 179.86 K | INSAT-3DR `IMG_TIR1_TEMP` calibration LUT demonstrates inverse radiance-to-temperature mapping: Count 0 is warm (340.06 K); Count 920 is 180.16 K; Count 921 to 1023 is clamped to the minimum floor 179.86 K. The implementation in `crop_engine.py` (`clamped_count_min: 921`) is scientifically exact. F2.3R text suffered from an inversion assumption. | **REPORTING_ERROR** |

---

## 2. In-Depth Forensic Findings

### Discrepancy 2.1 — Frozen Manifest Checksum
- **Physical Manifest Path:** `data/manifests/vayumarg_f1_1_freeze_manifest.json`
- **Physical Size:** 1,777 bytes
- **Actual SHA-256:** `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`
- **History:** First established in Milestone F1.1, audited in F2.1, F2.2, F2.3, and verified in `reports/F2_3R_BASELINE_AUDIT.md`. In `reports/F2_3R_ACCEPTANCE.md`, an erroneous hash starting with `441ab500be2e...` was typed. The file on disk has remained bit-perfect and untouched.
- **Verdict:** Clean. No data alteration.

### Discrepancy 2.2 — Multichannel Processed Crop Checksum
- **Physical Crop Path:** `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5`
- **Physical Size:** 633,554 bytes
- **Actual SHA-256:** `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90`
- **History:** Generated in Milestone F2.2. Referenced consistently in `F2_2_ACCEPTANCE.md`, `F2_3_BASELINE_AUDIT.md`, and `F2_3R_BASELINE_AUDIT.md`. An erroneous string starting with `7649f85d...` was transcribed in `reports/F2_3R_ACCEPTANCE.md`. The physical HDF5 file on disk was never modified.
- **Verdict:** Clean. No data alteration.

### Discrepancy 2.3 — Historical Database Provenance
- Direct PostgreSQL queries against `vayumarg` confirmed:
  - `SELECT COUNT(*) FROM storms;` -> **1,860** rows.
  - `SELECT COUNT(*) FROM track_observations;` -> **104,374** rows.
  - Foreign key check: All 1,860 storms link to authentic observations.
  - Synthetic data segregation: Table `storms` and table `track_observations` contain **ZERO** synthetic records. Synthetic fixtures were introduced in F2.1 strictly in `satellite_granules` (1 row), `satellite_processed_crops` (12 rows), and `satellite_track_associations` (21 rows).
  - Narrative confusion in F2.3R arose because 1,860 - 13 (crops) = 1,847, leading to a false claim in report prose that 13 storms were synthetic.
- **Verdict:** Clean. Scientific database integrity is 100% authentic.

### Discrepancy 2.4 — Image Geometry & Spatial Quantization
- Inspection of `REMAL_20240526_1802_MULTICHANNEL.h5`:
  - Output shape: `(4, 201, 201)`.
  - Target spatial extent: 800 km ($[-400\text{ km}, +400\text{ km}]$ around storm center).
  - Target grid resolution: 4.0 km (native to TIR-1, TIR-2, MIR).
  - WV channel (native 8.0 km) is resampled via normalized bilinear interpolation to the common 4.0 km grid without inflating effective physical resolution.
  - Spatial offset: At 2024-05-26 18:02 UTC, the IMD storm center (21.70°N, 89.20°E) was located exactly **1.03 km** from the nearest discrete pixel center on the INSAT-3DR grid. F2.3R reports mistakenly conflated this 1.03 km offset distance with native pixel resolution.
- **Verdict:** Clean. 201x201 at 4.0 km is the canonical, verified geometry.

### Discrepancy 2.5 — Remal Storm Center Coordinates
- The official IMD Best Track observation at 2024-05-26 18:00 UTC:
  - Latitude: **21.70°N**, Longitude: **89.20°E**.
  - Wind speed: 60 kts (Severe Cyclonic Storm), Pressure: 978 hPa.
  - Distance to INSAT-3DR crop center (21.70°N, 89.21°E): **1.03 km**.
- JTWC Best Track observation at 2024-05-26 18:00 UTC:
  - Latitude: 22.20°N, Longitude: 88.50°E, Wind: 55 kts, Pressure: 979 hPa.
  - Distance to crop center: 91.94 km.
- The reference in F2.3R text to 20.90°N was an accidental citation of an earlier observation during Remal's transit across the central Bay of Bengal (~12:00 UTC).
- **Verdict:** Clean. The actual database records and crop metadata reflect the correct 21.70°N, 89.20°E location.

### Discrepancy 2.6 — Calibration LUT Inversion & Clamping
- INSAT-3DR L1B Imager calibration follows an inverted scale for thermal infrared radiances:
  - High digital count = Low scene radiance / cold brightness temperature.
  - Low digital count = High scene radiance / warm brightness temperature.
- Direct inspection of `IMG_TIR1_TEMP` dataset in `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`:
  - `lut[0] = 340.06 K`
  - `lut[920] = 180.16 K`
  - `lut[921] = 179.86 K` (calibration lower floor)
  - `lut[922..1023] = 179.86 K` (constant floor clamping)
- Code in `crop_engine.py`:
  - Line 34: `clamped_count_min: 921`
  - Line 352: `clamped_mask = native_counts >= cfg["clamped_count_min"]`
- The code is 100% radiometrically accurate. The statement in F2.3R text that count 0 mapped to 179.86 K was a conceptual error in the narrative.
- **Verdict:** Clean. Exact calibration logic confirmed.

---

## 3. Gate Zero Final Conclusion

All six issues have been rigorously investigated and confirmed to be **`REPORTING_ERROR`** instances in narrative documentation, with **zero** defects in the actual scientific database, physical data files, or satellite processing algorithms.

- **Data Integrity Blockers:** **0**
- **Unresolved Issues:** **0**
- **Gate Zero Status:** **PASSED — AUTHORIZED TO PROCEED TO DOWNLOAD RECOVERY ARCHITECTURE**

