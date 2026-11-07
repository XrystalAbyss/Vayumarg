# Vayumarg F2.4 Gate C1R — Cyclone BIPARJOY SID Forensic Investigation

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate C1R — Scientific Metadata Closure & Gate D Preflight  
**Auditor:** Principal Scientific Data Architect, Dataset Governance Specialist, QA Lead  
**Investigation Target:** Discrepancy between reported IBTrACS SID (`2023157N13066`) and authoritative SID (`2023156N10067`)  
**Outcome Classification:** **`REPORTING_ONLY_ERROR`** (Verified Clean Database State)  

---

## 1. Background & Scope of Investigation

The Gate C acceptance report and Multi-Storm QC document cited:
> *BIPARJOY IBTrACS Consensus: `2023157N13066`*

However, the official NOAA/NCDC IBTrACS v04r01 database registers Cyclone BIPARJOY as:
> *Canonical SID: `2023156N10067`*  
> Authoritative URL: [https://ncics.org/ibtracs/index.php?name=v04r01-2023156N10067](https://ncics.org/ibtracs/index.php?name=v04r01-2023156N10067)

This triggered an immediate forensic audit across:
1. The imported raw NOAA CSV file (`data/raw/ibtracs_ni_v04r01.csv`).
2. PostgreSQL tables: `storms`, `storm_aliases`, `track_observations`, `satellite_processed_crops`, and `satellite_track_associations`.
3. The ingestion scripts and crop metadata dictionaries.

---

## 2. Forensic Findings

### 2.1 Inspection of Original NOAA Source CSV
A full text scan of `data/raw/ibtracs_ni_v04r01.csv` revealed:
- **Line 61604:** `SID = 2023156N10067`, `NAME = BIPARJOY`, `SEASON = 2023`, `BASIN = NI`.
- Search for `2023157N13066` yielded **0 matches**. The string does not exist in any NOAA raw data asset.

### 2.2 Inspection of PostgreSQL Research Database (`vayumarg`)
Direct SQL queries against the database revealed:
```sql
SELECT id, canonical_name, season_year, primary_basin FROM storms WHERE canonical_name = 'BIPARJOY';
-- Result:
-- ID: b343731d-ed85-4d1b-ab83-27b4210ba5e0 | Name: BIPARJOY | Year: 2023 | Basin: NI

SELECT source_agency, agency_storm_id, agency_storm_name FROM storm_aliases WHERE storm_id = 'b343731d-ed85-4d1b-ab83-27b4210ba5e0';
-- Results:
-- Agency: IBTRACS | AgencyStormID: 2023156N10067 | Name: BIPARJOY
-- Agency: JTWC    | AgencyStormID: IO022023      | Name: BIPARJOY

SELECT * FROM storm_aliases WHERE agency_storm_id = '2023157N13066';
-- Result: 0 rows (Empty set)
```

### 2.3 Inspection of Crop Foreign Key & Associations
In `satellite_processed_crops`:
- Crop `fc074478-42dd-4d02-b86f-8eb109cc9872` (`BIPARJOY_20230612_2358_MULTICHANNEL.h5`) references foreign key `storm_id = 'b343731d-ed85-4d1b-ab83-27b4210ba5e0'`, exactly matching canonical BIPARJOY.
- The linked track observations at `2023-06-13 00:00:00 UTC` correspond to row 61669:
  - IMD: $20.6^\circ\text{N}$, $67.0^\circ\text{E}$ | 85 kt | 962 hPa | VSCS
  - JTWC: $20.7^\circ\text{N}$, $67.0^\circ\text{E}$ | 85 kt | 961 hPa
  - IBTRACS: $20.7^\circ\text{N}$, $67.0^\circ\text{E}$ | 85 kt | 962 hPa
- Raw payloads for all three track observations explicitly record:
  `'sid': '2023156N10067'`.

---

## 3. Root Cause Analysis & Outcome Classification

The erroneous string `2023157N13066` originated purely as a typographical hallucination during the composition of the markdown document `reports/F2_4_GATE_C_MULTISTORM_QC.md`. 

- **No database table, column, metadata field, or JSON attribute ever contained `2023157N13066`.**
- **The actual image was never associated with an incorrect storm.**
- **Foreign key integrity between crop, storm, aliases, and track observations is 100% sound.**

### Classification:
**`REPORTING_ONLY_ERROR`**

---

## 4. Remediation Actions

1. **Markdown Report Correction:** `reports/F2_4_GATE_C_MULTISTORM_QC.md` line 90 has been updated to cite canonical SID `2023156N10067`.
2. **Regression Test Suite Enhancement:** Added automated test `test_biparjoy_canonical_sid_and_alias_resolution` to assert that BIPARJOY crops in PostgreSQL strictly resolve to canonical SID `2023156N10067` and reject any erroneous SID variants.

