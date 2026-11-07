# Scientific Data Contract for Tropical Cyclone Research (Vayumarg)

**Target Audience:** Module A (Current-State Estimation) and Module B (Track Forecasting) Teams  
**Authority:** Principal Scientific Software Architect & Lead Meteorologist  
**Status:** Hardened Data Contract (Milestone F0.1)  

---

## 1. Overview & Purpose

This document establishes the binding scientific conventions and data contracts governing all tropical cyclone observations, satellite alignments, quality assessments, and modeling datasets within the Vayumarg platform. 

Both Module A (Ishhan, Ishika, Kirti) and Module B (Chandan, Khushi, Hiten) must strictly conform to these rules. **Under no circumstances should any team alter, convert, or harmonize meteorological parameters without an officially approved and validated scientific transformation.**

---

## 2. Storm Identifiers & Basin Governance

### 2.1 Basin Classifications
The North Indian Ocean (NIO) basin is partitioned into two distinct regional basins:
- **`BOB` (Bay of Bengal):** Waters north of the equator, bounded by the east coast of India, Sri Lanka, Bangladesh, Myanmar, and the Malay Peninsula (approx. longitude 77°E to 100°E).
- **`ARB` (Arabian Sea):** Waters north of the equator, bounded by the west coast of India, Pakistan, Iran, the Arabian Peninsula, and Somalia (approx. longitude 50°E to 77°E).
- **`NIO`:** Reserved strictly for legacy datasets where historical tracks traverse or combine both sub-basins without distinction.

### 2.2 Canonical Storm Identity & Unnamed Storm Policy
- **Primary Key Invariant:** Every canonical cyclone system is assigned an immutable internal UUID primary key (`storms.id`).
- **Coexistence of Unnamed Cyclones:** In tropical cyclone climatology (especially in the North Indian Ocean), numerous systems never reach named intensity and remain designated as `UNNAMED`, `DEPRESSION`, or `DEEP DEPRESSION`.
  - **Rule:** Multiple unnamed storms within the same season and basin must freely coexist as distinct entities in `storms`.
  - **Rule:** Two distinct storms sharing the same canonical name (e.g. across basins or re-used names across seasons) must freely coexist as distinct entities.
- **Authoritative Source Identifiers:** Source-specific storm identities are retained in `storm_aliases`:
  - **IBTrACS SID:** The NOAA Storm Identifier (e.g., `2020136N10087`) is unique per storm event within the IBTrACS namespace (`source_agency = 'IBTRACS'`).
  - **IMD Cyclone Code:** IMD operational codes (e.g., `BOB 01/2024`) are unique within the IMD namespace (`source_agency = 'IMD'`).
  - **Alias Conflicts:** Attempting to assign an existing source identifier to a different storm violates `UNIQUE(source_agency, agency_storm_id)`. Such occurrences indicate a genuine catalog collision and must be flagged for manual scientific review; **distinct storms must never be silently merged based on similarity of name, dates, or coordinates alone.**

---

## 3. Spatial & Temporal Standards

### 3.1 Temporal Standards (Strict UTC)
- **Universal Requirement:** All timestamps stored or transmitted across contracts must be **explicitly UTC-aware** (`datetime(..., tzinfo=timezone.utc)`). Naive timestamps or local IST/EST timestamps are rejected at the contract boundary.
- **Timestamp Distinctions:**
  1. `observation_time_utc`: The valid synoptic time of the cyclone observation (standard synoptic hours: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC).
  2. `retrieval_time_utc`: The exact UTC wall-clock time when Vayumarg retrieved or scraped the source asset.
  3. `data_availability_time_utc`: The time at which the observation or advisory was officially released to the public or operational forecasters. If unknown, it must remain `NULL`; **never invent or assume data availability times.**

### 3.2 Geospatial Coordinate Conventions
- Coordinate Reference System: **WGS84 (EPSG:4326 / SRID 4326)**.
- Ordering: **Longitude / Latitude** for PostGIS geometric constructors (`ST_MakePoint(longitude, latitude)`).
- Valid Physical Ranges:
  - Latitude: `[-90.0, +90.0]` degrees (positive North, negative South).
  - Longitude: `[-180.0, +180.0]` degrees (positive East, negative West).

---

## 4. Wind Speed & Intensity Conventions

### 4.1 Sustained Wind Averaging Periods (CRITICAL)
Different meteorological agencies operate under fundamentally different physical conventions for Maximum Sustained Surface Winds (MSW):

| Agency / Center | Averaging Period | Reference Height | Standard Reference |
| :--- | :--- | :--- | :--- |
| **IMD (RSMC New Delhi)** | **3-minute sustained** | 10 meters above open sea | IMD Cyclone Warning SOP |
| **JTWC / NHC (USA)** | **1-minute sustained** | 10 meters above open sea | US Saffir-Simpson / JTWC ATCF |
| **WMO Standard / JMA / BOM** | **10-minute sustained** | 10 meters above open sea | WMO Technical Document No. 558 |

**Scientific Invariant:**
- 1-minute sustained wind speeds are mathematically and physically higher than 3-minute sustained wind speeds for the exact same storm state (typical ratio ~ 1.11 to 1.14 depending on gust factors).
- **Rule:** Under no circumstance should a 1-minute wind be stored as an IMD wind, or an IMD 3-minute wind be directly compared to JTWC without explicit conversion.
- `track_observations` maintains separate records for each agency reporting on the same storm at the same synoptic hour.

### 4.2 Official IMD Cyclone Intensity Scale
Reference: *India Meteorological Department (RSMC New Delhi) Standard Operating Procedure for Cyclone Warning.*

| IMD Category Code | Full Category Name | 3-Minute MSW (knots) | 3-Minute MSW (km/h) |
| :--- | :--- | :--- | :--- |
| **LOW** | Low Pressure Area | < 17 kt | < 31 km/h |
| **D** | Depression | 17 – 27 kt | 31 – 49 km/h |
| **DD** | Deep Depression | 28 – 33 kt | 50 – 61 km/h |
| **CS** | Cyclonic Storm | 34 – 47 kt | 62 – 88 km/h |
| **SCS** | Severe Cyclonic Storm | 48 – 63 kt | 89 – 117 km/h |
| **VSCS** | Very Severe Cyclonic Storm | 64 – 89 kt | 118 – 166 km/h |
| **ESCS** | Extremely Severe Cyclonic Storm | 90 – 119 kt | 167 – 221 km/h |
| **SuCS** | Super Cyclonic Storm | $\ge$ 120 kt | $\ge$ 222 km/h |

### 4.3 Missing Data Policy
- Incomplete or missing observations must be recorded as **`NULL` (`None`)**, never `0.0`.
- An observation with `wind_speed_knots = 0` and `central_pressure_hpa = 940` is an invalid data corruption artifact and will be rejected by the quality validator.

---

## 5. Source Revision & Lineage Policy

### 5.1 Deterministic Observation Identity
Within any raw source file (`source_asset_id`), each row is assigned a deterministic `source_record_id` (e.g. line number or composite `{SID}_{ISO_TIME}`).
- Database constraint: `UNIQUE(source_asset_id, source_record_id)` prevents accidental double-ingestion.

### 5.2 Preservation of Re-Analyzed Best-Track Releases
- Operational cyclone bulletins are often revised months after an event when post-season best-track re-analysis is completed (e.g., NOAA IBTrACS release v04r01 superseding v04r00).
- **Revision Invariant:** When a revised source asset is ingested:
  1. The new asset is registered with its own unique SHA-256 in `source_assets`.
  2. Revised observations are inserted linked to the new `source_asset_id`.
  3. Previous observations from the superseded asset are retained in full and flagged with `is_superseded = TRUE`.
  4. **Observations from older snapshots are NEVER silently overwritten or deleted.**
  5. Consumers seeking the authoritative current best-track filter on `WHERE NOT is_superseded`. Consumers seeking real-time operational simulation evaluate only the unrevised operational advisories available at forecast issuance.

---

## 6. Dataset Split Governance (Storm-Level Partitioning)

- Random row-level train/test splits are **strictly prohibited** in tropical cyclone modeling.
- Temporal or spatial autocorrelation across 3-hour or 6-hour track points causes catastrophic data leakage if track points from the same cyclone event appear in both training and test sets.
- **Rule:** Splits must be performed strictly at the **storm level** (e.g., Holdout Seasons: 2023–2024; Training Seasons: 2000–2022).
- No arbitrary split scripts may be committed until Milestone F2. All dataset snapshots must register an immutable manifest in `dataset_snapshots` with SHA-256 verification.
