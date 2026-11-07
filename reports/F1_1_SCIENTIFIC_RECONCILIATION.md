# VAYUMARG — F1.1 Scientific Data Reconciliation Report

**Milestone:** F1.1 — Scientific Data Reconciliation, Agency Wind Corrections and Reproducible Dataset Freeze  
**Execution Date:** 2026-11-01  
**Target Environment:** Windows 11 / PowerShell / Python 3.12 / PostgreSQL 16.4 / PostGIS 3.4.3 (Port 5433)  
**Database Name:** `vayumarg` (Persistent Research Database)  
**Test Database Name:** `vayumarg_test` (Isolated Discardable Database)  

---

## 1. Executive Summary

Milestone **F1.1** successfully executes a comprehensive scientific audit, provenance reconciliation, and cryptographic dataset freeze across the complete historical North Indian Ocean cyclone best-track database.

Key accomplishments:
1. **WMO Wind Provenance Reconciliation:** Corrected the foundational assumption that `WMO_WIND` carries a universal 10-minute averaging convention. Using official NOAA IBTrACS column documentation, `WMO_WIND` was dynamically mapped to its reporting agency (`WMO_AGENCY`): 7,042 records from RSMC New Delhi (IMD) reconciled to **3-minute sustained**; 645 records from RSMC Tokyo (JMA) confirmed as **10-minute sustained**; 243 records from US NHC/ATCF reconciled to **1-minute sustained**; and 70,583 observations with missing wind speeds correctly classified as **unknown**.
2. **IMD Four-Way Venn Reconciliation:** Resolved the apparent 51-count discrepancy between non-null wind observations (9,467) and IMD severity grades (9,518 standard, 9,558 total). Verified exact mathematical conservation across all 10,759 IMD records.
3. **Geospatial Cross-Basin Classification:** Investigated the extreme coordinate bounds (0.7° to 83.0°N, -87.7° to 163.7°E), identifying 7,707 synoptic track points outside the standard North Indian Ocean regional box (0–40°N, 30–105°E) belonging to 91 trans-basin and extratropical transition cyclones.
4. **Data Quality Issues Table Population:** Identified why `data_quality_issues` contained 0 records in F1. Populated meaningful scientific issue logs covering cross-basin tracks, uninstrumented maritime eras, and extreme coordinate anomalies.
5. **Real-Source Direct Verification:** Deterministically matched raw CSV lines directly against PostgreSQL database records across six benchmark eras (1842, 1932, 1951, 1966 Hurricane Faith, 2020 AMPHAN, 2023 BIPARJOY) with 100% coordinate and metadata agreement.
6. **Dataset Snapshot Manifest Freeze:** Generated an immutable, cryptographically verified dataset manifest at `data/manifests/vayumarg_f1_1_freeze_manifest.json` with SHA-256 hash `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`, locking the canonical training and validation baseline for Module A and Module B.

---

## 2. Investigation and Correction of WMO_WIND Provenance

### The Scientific Issue
In milestone F1, all 62,885 observations ingested under `source_agency == 'IBTRACS'` were assigned an `averaging_period` of `'10-min'`. Official NOAA IBTrACS documentation explicitly states:

> *"The WMO columns represent the official values provided by the WMO regional center designated for that basin... WMO_WIND does not have a single standard averaging period; its averaging period corresponds to that used by the agency specified in WMO_AGENCY."*

### Empirical Finding Across 62,885 Raw IBTrACS Observations
Querying the raw CSV and database payloads revealed:
- `WMO_WIND` is populated in **7,930 rows** (and NULL in 54,955 rows).
- When `WMO_WIND` is populated, `WMO_AGENCY` breaks down as follows:
  - **`newdelhi`:** 7,042 observations (88.80%). These are identical to `NEWDELHI_WIND` compiled by IMD. In meteorological science, RSMC New Delhi measures winds using a **3-minute sustained** averaging period.
  - **`tokyo`:** 645 observations (8.13%). RSMC Tokyo (JMA) measures winds using a **10-minute sustained** averaging period.
  - **`hurdat_atl`:** 242 observations (3.05%). National Hurricane Center (NHC) measures winds using a **1-minute sustained** averaging period.
  - **`atcf`:** 1 observation (0.01%). JTWC/ATCF standard is **1-minute sustained**.
- When `WMO_WIND` is NULL (54,955 rows), `WMO_AGENCY` is blank. F1 erroneously labeled these empty observations as 10-minute winds.

### Scientific Impact Before and After Reconciliation

| Sustained Averaging Period | Pre-F1.1 Baseline Count | Post-F1.1 Reconciled Count | Net Scientific Adjustment |
| :--- | :--- | :--- | :--- |
| **`3-min` sustained** | 10,759 | **16,509** | **+5,750** (7,042 WMO New Delhi added; 1,292 null-wind IMD reclassified) |
| **`1-min` sustained** | 30,730 | **16,637** | **-14,093** (243 WMO NHC/ATCF added; 14,336 null-wind JTWC reclassified) |
| **`10-min` sustained** | 62,885 | **645** | **-62,240** (Correctly isolated to RSMC Tokyo JMA records) |
| **`unknown` (NULL wind)** | 0 | **70,583** | **+70,583** (Rigorous scientific labeling of missing wind records) |
| **Total Observations** | **104,374** | **104,374** | **Exact Population Balance Verified** |

---

## 3. IMD Four-Way Venn Population Reconciliation

### The Discrepancy Investigated
F1 reported two conflicting counts in adjacent tables:
- Table 3 (Observations with non-null wind): `9,467`
- Table 4 (Observations with IMD categories): `9,518` (standard) + `40` (historical/regional) = `9,558`
The apparent discrepancy was `9,518 - 9,467 = +51` observations.

### Four-Way Partition Analysis
The complete population of 10,759 observations from IMD was partitioned into four mutually exclusive, collectively exhaustive subsets:

| Subset ID | Population Description | Count | Percentage |
| :--- | :--- | :--- | :--- |
| **Set A** | Both Wind Speed and IMD Category Populated | **8,397** | 78.05% |
| **Set B** | IMD Category Populated, but Wind Speed is NULL | **1,161** | 10.79% |
| **Set C** | Wind Speed Populated, but IMD Category is NULL | **1,070** | 9.95% |
| **Set D** | Neither Wind Speed nor IMD Category Populated | **131** | 1.22% |
| **Total** | **All Ingested IMD Track Observations** | **10,759** | **100.00%** |

### Mathematical Proof of the 51-Count Difference
- **Non-Null Wind Denominator (Table 3):**  
  $$\text{Set A} + \text{Set C} = 8,397 + 1,070 = 9,467$$
- **Populated Category Denominator (Table 4):**  
  $$\text{Set A} + \text{Set B} = 8,397 + 1,161 = 9,558$$
- Decomposing the 9,558 category records:
  - Standard WMO Grades (`D`, `DD`, `CS`, `SCS`, `VSCS`, `ESCS`, `SuCS`): **9,518**
  - Regional/Historical Grades (`SCS(H)`: 27, `SUCS`: 9, `L`: 4): **40**
- Subtracting non-null wind from standard grades:
  $$9,518 - 9,467 = 51$$
The 51-count difference is not a data omission; it represents the exact net difference between observations that recorded cyclone stage estimates without measured anemometer winds (1,161) versus observations that recorded anemometer winds during unnamed/undifferentiated phases without formal stage labels (1,070), minus the 40 historical codes:
$$1,161 - 1,070 - 40 = 51$$

---

## 4. Geospatial Domain & Cross-Basin Cyclone Dynamics

### The Extreme Geographic Envelope
The raw North Indian Ocean archive contains points spanning:
- Latitude: `0.70°N` to `83.00°N`
- Longitude: `-87.70°W` to `163.70°E`

### Root-Cause Analysis
NOAA IBTrACS tracks storms across their entire meteorological life cycle. When a storm traverses multiple ocean basins or undergoes extratropical transition, IBTrACS includes the entire contiguous track in each basin list where the storm spent significant lifetime.

In the North Indian Ocean dataset (`ibtracs.NI.list.v04r01.csv`):
- **Regional North Indian Ocean Box (0–40°N, 30–105°E):** 96,667 observations (92.62%).
- **Cross-Basin / Trans-Oceanic Points:** 7,707 observations (7.38%) across 91 storms.

Notable instances:
1. **Hurricane Faith (1966, SID `1966233N13340`):** Reached **83.0°N**, transiting across the Arctic Ocean into the Siberian sector of Northern Eurasia.
2. **Storm 1932244N19296 (1932):** Track originated in the Caribbean Sea at **-63.6°W**, transited Central America, the Pacific, and into the Arabian Sea.
3. **Western Pacific Transits:** Numerous typhoons originating in the South China Sea (110°–130°E) cross the Malay Peninsula into the Bay of Bengal.

### Engineering Resolution
- All 7,707 cross-basin track observations were classified with `quality_flag = 'CROSS_BASIN'` via forward Migration `004_wmo_agency_and_quality_audit.py`.
- Regional observations (96,667) maintain `quality_flag = 'VALID'`.

---

## 5. Data Quality Issues Subsystem Resolution

### Root Cause in F1
In F1, `src/vayumarg/quality/validator.py` performed in-memory quality checks and returned status dictionaries, but never inserted rows into the `data_quality_issues` database table. Consequently, `SELECT count(*) FROM data_quality_issues` returned `0`.

### Reconciled Implementation
In F1.1, `execute_scientific_reconciliation()` explicitly persists structured scientific quality records in `data_quality_issues`:
1. **`CROSS_BASIN_TRACK_POINTS` (WARNING):** 7,707 synoptic points flagged with bounding box criteria, accepted under `ACCEPTED_EXCEPTION` status.
2. **`HISTORICAL_UNINSTRUMENTED_ERA` (INFO):** 265 pre-1900 storms derived from maritime logs with NULL surface wind fields.
3. **`UNNAMED_CYCLONE_POPULATION` (INFO):** 1,713 cyclones pre-dating the WMO/ESCAP 2004 naming convention.
4. **`ARCTIC_EXTRATROPICAL_TRANSITION` (INFO):** Specific sample records documenting extreme high-latitude transits (e.g. Hurricane Faith points at lat $\ge 80^\circ$N).

---

## 6. Real-Source Direct Verification Across Six Eras

A dedicated reconciliation verification script (`scripts/verify_raw_reconciliation.py`) deterministically compared raw CSV lines from `data/raw/ibtracs_ni_v04r01.csv` against PostgreSQL database records:

| Meteorological Era | Storm SID | Storm Name | Year | Raw CSV Rows | Database Observations | Coordinate Match | Verified Conventions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1842 Uninstrumented** | `1842298N11080` | `UNNAMED` | 1842 | 65 | 65 | **100% Exact** | Null wind preserved as `unknown` |
| **1932 Cross-Basin** | `1932141N12074` | `UNNAMED` | 1932 | 18 | 18 | **100% Exact** | Multi-agency track preserved |
| **1951 Pre-Satellite** | `1951105N08069` | `UNNAMED` | 1951 | 60 | 119 | **100% Exact** | IBTRACS + JTWC coexistence |
| **1966 Arctic Cross-Basin** | `1966233N13340` | `FAITH` | 1966 | 191 | 382 | **100% Exact** | `hurdat_atl` 1-min wind, `CROSS_BASIN` flag |
| **2020 Modern Super Cyclone**| `2020136N10088` | `AMPHAN` | 2020 | 51 | 146 | **100% Exact** | `newdelhi` 3-min wind, IMD `SuCS` category |
| **2023 Modern Severe Cyclone**| `2023156N10067` | `BIPARJOY`| 2023 | 113 | 316 | **100% Exact** | 3-min IMD + 1-min JTWC dual tracking |

---

## 7. Cryptographic Dataset Snapshot Freeze

The complete reconciled dataset was frozen into a reproducible snapshot:
- **Snapshot ID:** `c36a218a-09db-4bec-a02f-da546b83df02`
- **Snapshot Name:** `vayumarg-nio-ibtracs-f1.1-freeze`
- **Transformation Version:** `f1.1`
- **Manifest File:** `data/manifests/vayumarg_f1_1_freeze_manifest.json`
- **Manifest SHA-256:** `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`
- **Total Samples Locked:** `104,374`

---

## 8. Machine Learning Model Readiness & Independence Guarantee

### Module A (Satellite-Based Current State Estimation)
- **Target Contract:** `ModuleAExportRecord` via `vayumarg.contracts.export.export_module_a_dataset`.
- **Wind Ground Truth:** IMD 3-min sustained wind (`imd_wind_speed_knots`), JTWC 1-min sustained wind (`jtwc_wind_speed_knots`), and WMO provenance-aware wind (`wmo_wind_speed_knots`).
- **Satellite Epoch:** 464 storms (1982–2026) ready for spatial-temporal pairing with INSAT-3D/3DR and METEOSAT rasters.

### Module B (Track and Intensity Forecasting)
- **Target Contract:** `ModuleBExportRecord` via `vayumarg.contracts.export.export_module_b_dataset`.
- **Trajectory Sequence Ground Truth:** 1,860 complete storm trajectories with up to 113 consecutive synoptic steps per storm.
- **Independence Guarantee:** Module B models consume strictly historical best-track trajectories ($t \le t_0$) and external meteorological reanalysis. They contain zero architectural dependencies on Module A inference outputs.
- **Domain Recommendation:** Regional track models should train on `quality_flag == 'VALID'` records (96,667 points) to avoid extratropical/Arctic bias.

