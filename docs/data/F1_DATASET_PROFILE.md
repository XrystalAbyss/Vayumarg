# North Indian Ocean Cyclone Database Profile (F1 Baseline)

## 1. Dataset Profile Overview

The Vayumarg canonical database (`vayumarg`) hosts the complete historical best-track archive for the North Indian Ocean basin extracted from NOAA IBTrACS v04r01.

| Attribute | Verified Value |
| :--- | :--- |
| **Canonical Database Name** | `vayumarg` |
| **Spatial Engine** | PostgreSQL 16.4 / PostGIS 3.4.3 (SRID 4326) |
| **Total Registered Cyclones (Storms)** | **1,860** |
| **Total Cross-Agency Aliases** | **2,534** |
| **Total Synoptic Track Observations** | **104,374** |
| **Temporal Span** | **1842-10-25 03:00 UTC to 2026-10-28 12:00 UTC** |
| **Temporal Coverage** | **185 Seasons (1842 – 2026)** |
| **Geographic Envelope** | Latitude: `[0.70°, 83.00° N]`, Longitude: `[-87.70°, 163.70° E]` |

---

## 2. Storm Registry Demographics

### Named vs Unnamed Cyclones
- **Named Storms:** `147` (7.9%)
- **Unnamed Storms:** `1,713` (92.1%)

*Meteorological Context:* Cyclone naming in the North Indian Ocean was officially instituted by the WMO/ESCAP Panel on Tropical Cyclones (PTC) in **September 2004** (Cyclone Onil was the first officially named storm). All pre-2004 disturbances and post-2004 depressions that did not reach cyclonic storm threshold are recorded as `UNNAMED`.

### Temporal Distribution Across Meteorological Eras
1. **Historical / Pre-Modern Era (1842 – 1899):** `265 storms`
   - Compiled primarily from historical ship logs, East India Company maritime archives, and early Calcutta/Bombay observatory bulletins.
2. **Conventional Instrument Era (1900 – 1981):** `1,131 storms`
   - Coastal synoptic stations, ship radio observations, and coastal radar stations (installed post-1970).
3. **Modern Satellite Era (1982 – Present):** `464 storms`
   - Comprehensive satellite coverage from INSAT-1, INSAT-2, INSAT-3D/3DR, METEOSAT, and polar-orbiting radiometers (MODIS, VIIRS, SSM/I).

---

## 3. Observation Agency Breakdown & Reconciled Averaging Periods

Every synoptic observation record is partitioned by its reporting agency and standard sustained wind averaging convention:

| Source Agency | Sustained Wind Averaging Convention | Total Observations Stored | Observations with Non-Null Wind Speed |
| :--- | :--- | :--- | :--- |
| **`IBTRACS`** | Dynamic by `WMO_AGENCY`: `newdelhi` (3-min), `tokyo` (10-min), `hurdat_atl` (1-min) | **62,885** | 7,930 |
| **`JTWC`** (`USA`) | `1-min` sustained (US standard) | **30,730** | 16,394 |
| **`IMD`** (`NEWDELHI`) | `3-min` sustained (RSMC New Delhi standard) | **10,759** | 9,467 |
| **Total** | Multi-Agency Partitioned | **104,374** | **33,791** |

### Averaging Period Breakdown Across Full Database (Post-F1.1 Reconciliation)

- **`3-min` sustained:** `16,509` (IMD 9,467 + IBTRACS New Delhi 7,042)
- **`1-min` sustained:** `16,637` (JTWC 16,394 + IBTRACS HURDAT 242 + IBTRACS ATCF 1)
- **`10-min` sustained:** `645` (IBTRACS Tokyo / JMA 645)
- **`unknown`:** `70,583` (Historical uninstrumented / NULL wind observations across agencies)
- **Total Balance:** `16,509 + 16,637 + 645 + 70,583 = 104,374` (100% exact)

---

## 4. IMD Cyclone Classification Distribution & Venn Reconciliation

Observations containing official IMD severity grades (`imd_category`):

| IMD Grade | Severity Name | Sustained Wind Criteria (3-min) | Observed Track Points |
| :--- | :--- | :--- | :--- |
| **`D`** | Depression | 17 – 27 kts (31 – 49 km/h) | **3,994** |
| **`DD`** | Deep Depression | 28 – 33 kts (50 – 61 km/h) | **2,196** |
| **`CS`** | Cyclonic Storm | 34 – 47 kts (62 – 88 km/h) | **1,683** |
| **`SCS`** | Severe Cyclonic Storm | 48 – 63 kts (89 – 117 km/h) | **784** |
| **`VSCS`** | Very Severe Cyclonic Storm | 64 – 89 kts (118 – 166 km/h) | **691** |
| **`ESCS`** | Extremely Severe Cyclonic Storm | 90 – 119 kts (167 – 221 km/h) | **145** |
| **`SuCS`** | Super Cyclonic Storm | ≥ 120 kts (≥ 222 km/h) | **25** |
| Other | Regional Historical Sub-classifications (`SCS(H)`: 27, `SUCS`: 9, `L`: 4) | Historical | 40 |
| **Total Populated Category Points** | | | **9,558** |

### Four-Way IMD Population Partition (Denominators Reconciled)

- **Both Wind and Category Populated:** `8,397` (78.05%)
- **Category Populated with NULL Wind:** `1,161` (10.79%)
- **Wind Populated with NULL Category:** `1,070` (9.95%)
- **Neither Wind nor Category Populated:** `131` (1.22%)
- **Total IMD Observations:** `10,759` (100.00%)
- *Explanation of Discrepancy:* Non-null wind denominator (Table 3) = 8,397 + 1,070 = 9,467. Populated standard category denominator (Table 4) = 8,397 + 1,161 = 9,558 (9,518 standard WMO grades + 40 historical). Difference = 9,518 - 9,467 = +51. Exact four-way Venn verified.

---

## 5. Geospatial Domain & Cross-Basin Classification

- **Regional NI Track Points:** `96,667` (bounded by 0°–40°N, 30°–105°E)
- **Cross-Basin Track Points:** `7,707` (91 storms with tracks transiting into Western Pacific, Southern Indian Ocean, or Arctic extratropical transitions)
- **Extreme Coordinates:** Hurricane Faith (1966) at `83.0°N` (Arctic sector); Storm 1932244N19296 originating at `-63.6°W`.

---

## 6. Dataset Snapshot & Manifest Verification

- **Snapshot ID:** `c36a218a-09db-4bec-a02f-da546b83df02`
- **Snapshot Name:** `vayumarg-nio-ibtracs-f1.1-freeze`
- **Transformation Version:** `f1.1`
- **Manifest SHA-256:** `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`
- **Total Samples:** `104,374`
- **Manifest URI:** `data/manifests/vayumarg_f1_1_freeze_manifest.json`

---

## 5. Benchmark Benchmark Cyclones Verified

### 1. Super Cyclonic Storm AMPHAN (May 2020)
- **Authoritative IBTrACS SID:** `2020136N10088`
- **JTWC ATCF ID:** `IO012020`
- **Primary Basin / Subbasin:** `NI` / `BB` (Bay of Bengal)
- **Total Ingested Observations:** 146 observations (51 synoptic time steps)
- **Peak IMD Wind (3-min):** `130.0 kts`
- **Peak JTWC Wind (1-min):** `145.0 kts`
- **Minimum Central Surface Pressure:** `901.0 hPa`

### 2. Extremely Severe Cyclonic Storm BIPARJOY (June 2023)
- **Authoritative IBTrACS SID:** `2023156N10067`
- **JTWC ATCF ID:** `IO022023`
- **Primary Basin / Subbasin:** `NI` / `AS` (Arabian Sea)
- **Total Ingested Observations:** 316 observations (113 synoptic time steps)
- **Peak IMD Wind (3-min):** `90.0 kts`
- **Peak JTWC Wind (1-min):** `110.0 kts`
- **Minimum Central Surface Pressure:** `944.0 hPa`

