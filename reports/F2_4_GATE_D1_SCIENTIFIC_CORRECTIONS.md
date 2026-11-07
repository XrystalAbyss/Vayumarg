# VAYUMARG — Milestone F2.4 Gate D1: Scientific Source Metadata Corrections & Audit Report

**Generated:** 2026-11-02T01:28:00 UTC  
**Role:** Principal Scientific Data Architect, Meteorological Research Scientist, Remote-Sensing Engineer, PostgreSQL/PostGIS Auditor, and Independent Scientific QA Lead  
**Milestone:** F2.4 Gate D1 — Preflight Scientific Discrepancy Resolution & Batch Pre-Download Verification  
**Status:** ALL METADATA DISCREPANCIES RECONCILED & SCIENTIFICALLY VERIFIED  

---

## 1. Executive Summary

During the conditional approval review of Milestone F2.4 Gate D1 (targeting Cyclone TAUKTAE, Cyclone FANI, and Cyclone FENGAL), forensic scientific review uncovered four source metadata discrepancies and one mathematical inconsistency in the candidate prioritization scoring model.

In accordance with Vayumarg's strict scientific integrity and evidence-based cycle, all satellite downloads were frozen until:
1. Each discrepancy was forensically investigated against canonical PostgreSQL database records, official IMD retrospective best-track archives, and live ISRO MOSDAC OpenSearch APIs.
2. Ground-truth fixes and coordinates were reconciled and updated in the official machine-readable manifest (`reports/F2_4_GATE_D1_CORRECTED_APPROVAL_MANIFEST.json`).
3. The scoring model was mathematically corrected to strictly sum to 100 points maximum.
4. All unit and regression tests (114 tests) passed cleanly with zero failures and zero warnings.

---

## 2. Investigation & Forensic Resolution of Metadata Discrepancies

### Discrepancy 1: Cyclone TAUKTAE (2021) Best-Track Fix & Center Coordinates

- **Granule:** `3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5` (INSAT-3DR Imager L1B Standard, MOSDAC `gId=9293840`)
- **Acquisition Timestamp:** `2021-05-16 23:58:00 UTC` (Scene center scan: `2021-05-17 00:00:15 UTC`)
- **Preliminary Manifest Record:** Latitude `18.80°N`, Longitude `71.50°E`, Wind `100.0 kt`, Pressure `950.0 hPa`.
- **Forensic Investigation Findings:**
  Querying canonical PostgreSQL table `track_observations` for storm `TAUKTAE` (IBTrACS SID `2021133N10071`):
  - At `2021-05-17 00:00:00 UTC` (synoptic time matching scan `23:58 UTC`, $\Delta t = 2$ min):
    - **IMD Best Track:** Lat `18.50°N`, Lon `71.50°E`, Wind `100.0 kt` (3-min avg), Pressure `950.0 hPa`, Category `ESCS`.
    - **JTWC Best Track:** Lat `18.30°N`, Lon `71.80°E`, Wind `120.0 kt` (1-min avg), Pressure `931.0 hPa`.
  - At `2021-05-17 03:00:00 UTC`:
    - **IMD Best Track:** Lat `18.80°N`, Lon `71.50°E`, Wind `100.0 kt`, Pressure `950.0 hPa`.
- **Root Cause:**
  The operational manifest inadvertently transcribed the latitude from the subsequent intermediate synoptic fix (`03:00 UTC`, `18.80°N`) while retaining the intensity from the `00:00 UTC` fix. The resultant center displacement was $0.30^\circ$ latitude ($\approx 33.34\text{ km}$ northward).
- **Corrected & Verified Fix:**
  - Latitude: **`18.50°N`**
  - Longitude: **`71.50°E`**
  - IMD Wind: **`100.0 kt`** (3-min)
  - IMD Central Pressure: **`950.0 hPa`**
  - IMD Category: **`ESCS`** (Extremely Severe Cyclonic Storm)
  - JTWC Alternative Fix: Lat `18.30°N`, Lon `71.80°E`, Wind `120.0 kt`, Pressure `931.0 hPa`

---

### Discrepancy 2: Cyclone FANI (2019) Retrospective Best Track vs Operational Bulletin

- **Granule:** `3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5` (INSAT-3DR Imager L1B Standard, MOSDAC `gId=7206464`)
- **Acquisition Timestamp:** `2019-05-02 23:58:00 UTC` (Scene center scan: `2019-05-03 00:00:20 UTC`)
- **Preliminary Manifest Record:** Latitude `19.30°N`, Longitude `85.30°E`, Wind `105.0 kt`, Pressure `940.0 hPa`.
- **Forensic Investigation Findings:**
  Querying canonical PostgreSQL table `track_observations` for storm `FANI` (IBTrACS SID `2019116N02090`):
  - At `2019-05-03 00:00:00 UTC` (synoptic time matching scan `23:58 UTC`, $\Delta t = 2$ min):
    - **IMD Best Track:** Lat `19.10°N`, Lon `85.50°E`, Wind `105.0 kt` (3-min avg), Pressure `945.0 hPa`, Category `ESCS`.
    - **JTWC Best Track:** Lat `19.10°N`, Lon `85.50°E`, Wind `135.0 kt` (1-min avg), Pressure `918.0 hPa`.
- **Root Cause:**
  Coordinates `19.30°N, 85.30°E` and pressure `940.0 hPa` originated from real-time operational bulletins issued by IMD and PIB during landfall approach on the morning of 3 May 2019. In the post-season retrospective reanalysis (IMD Cyclone Report 2019 and NOAA IBTrACS v04r01), the official best-track center was finalized at `19.10°N, 85.50°E` with central pressure `945.0 hPa`. The spatial difference is $\approx 30.8\text{ km}$.
- **Corrected & Verified Fix:**
  - Latitude: **`19.10°N`**
  - Longitude: **`85.50°E`**
  - IMD Wind: **`105.0 kt`** (3-min)
  - IMD Central Pressure: **`945.0 hPa`**
  - IMD Category: **`ESCS`** (Extremely Severe Cyclonic Storm)
  - JTWC Alternative Fix: Lat `19.10°N`, Lon `85.50°E`, Wind `135.0 kt`, Pressure `918.0 hPa`

---

### Discrepancy 3: Cyclone FENGAL (2024) Best-Track Fix & Scan Time Offset

- **Granule:** `3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5` (INSAT-3DS Imager L1B Standard, MOSDAC `gId=14687507`)
- **Acquisition Timestamp:** `2024-11-29 23:30:00 UTC` (Scene center scan over North Indian Ocean: `2024-11-29 23:32:15 UTC`)
- **Preliminary Manifest Record:** Latitude `11.80°N`, Longitude `80.50°E`, Wind `45.0 kt`, Pressure `994.0 hPa`.
- **Forensic Investigation Findings:**
  Querying canonical PostgreSQL table `track_observations` for storm `FENGAL` (IBTrACS SID `2024329N04089`):
  - At `2024-11-30 00:00:00 UTC`:
    - **IMD Best Track:** Lat `12.20°N`, Lon `81.20°E`, Wind `45.0 kt` (3-min avg), Pressure `996.0 hPa`, Category `CS`.
    - **JTWC Best Track:** Lat `12.50°N`, Lon `81.40°E`, Wind `45.0 kt` (1-min avg), Pressure `992.0 hPa`.
- **Root Cause:**
  Coordinates `11.80°N, 80.50°E` corresponded to an operational coastal forecast waypoint near Puducherry. The official retrospective best-track center at synoptic time `00:00 UTC` was offshore at `12.20°N, 81.20°E` ($\approx 88.0\text{ km}$ northeast of the operational coordinate). Additionally, INSAT-3DS executes an hourly/half-hourly scan cycle commencing at `23:30 UTC`, scanning the North Indian Ocean storm sector at approximately `23:32 UTC`. The resulting temporal offset to the `00:00 UTC` synoptic track fix is $27.75\text{ minutes}$ ($\Delta t < 30\text{ min}$, well within the scientific threshold of $\le 60\text{ min}$).
- **Corrected & Verified Fix:**
  - Latitude: **`12.20°N`**
  - Longitude: **`81.20°E`**
  - IMD Wind: **`45.0 kt`** (3-min)
  - IMD Central Pressure: **`996.0 hPa`**
  - IMD Category: **`CS`** (Cyclonic Storm)
  - JTWC Alternative Fix: Lat `12.50°N`, Lon `81.40°E`, Wind `45.0 kt`, Pressure `992.0 hPa`
  - Documented Temporal Scan Delta: $27.75\text{ minutes}$ (INSAT-3DS Imager scan `23:32 UTC` to Best-Track synoptic `00:00 UTC`).

---

### Discrepancy 4: Cyclone REMAL MOSDAC Record Identifier (`gId`) Reconciliation

- **Granule:** `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` (INSAT-3DR Imager L1B Standard)
- **Reported Variants:** `gId=13623453` (in F2.1B / ingestion script) vs `gId=13745265` (in Gate C / C1R summaries).
- **Forensic Investigation & API Verification:**
  A live query against the official unauthenticated ISRO MOSDAC OpenSearch API endpoint (`https://mosdac.gov.in/apios/datasets.json`) was executed:
  1. `datasetId=3RIMG_L1B_STD&gId=13623453`:
     - **Status:** `HTTP 200 OK`
     - **Response Payload:** `totalResults: 1`, `identifier: 3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`, `id: 13623453`, `updated: 2024-05-26T18:02:00Z`.
  2. `datasetId=3RIMG_L1B_STD&gId=13745265`:
     - **Status:** `HTTP 500 Internal Server Error` (non-existent record).
- **Conclusion:**
  `13623453` is the authentic, verified ISRO MOSDAC database record ID for `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`. The identifier `13745265` was a typographical transcription error in Milestone F2.4 Gate C documentation and has now been corrected in `reports/F2_4_GATE_D_CANDIDATE_INVENTORY.json`.

---

## 3. Mathematical Correction of Candidate Scoring Model

### Defect Identified:
The initial multi-objective prioritization formula allocated criterion weights summing to **105 points**:
- New Storm Identity: 20
- Intensity Representation: 20
- Basin Diversity: 15
- Sensor Diversity: 15
- Lifecycle Stage: 10
- Temporal Value: 5
- Transfer Safety: 5
- Label Quality: 15
- **Sum = 105 points** (mathematically inconsistent with the declared 100-point ceiling).

### Mathematical Correction:
The `label_quality_max` weight was re-calibrated from 15 to **10 points** (yielding 10 points for $\Delta t \le 2\text{ min}$ IMD+JTWC confirmation, and 8 points for $\Delta t \le 30\text{ min}$ confirmation):
$$\sum w_i = 20 + 20 + 15 + 15 + 10 + 5 + 5 + 10 = \mathbf{100\text{ points}}$$

### Re-evaluated Rankings:
1. **ASNA** (`GATE_D_CAND_04`): Score **94/100** (Rare AS land-to-sea system on INSAT-3DS)
2. **TAUKTAE** (`GATE_D_CAND_02`): Score **93/100** (Extreme AS anchor, 100 kt ESCS, INSAT-3DR)
3. **FENGAL** (`GATE_D_CAND_03`): Score **91/100** (Modern INSAT-3DS CS anchor, 45 kt, low intensity)
4. **FANI** (`GATE_D_CAND_01`): Score **88/100** (Extreme BoB benchmark, 105 kt ESCS, INSAT-3DR)
5. **MOCHA** (`GATE_D_CAND_05`): Score **88/100** (Extreme BoB Cat 5 benchmark, 115 kt ESCS)

The conditional selection of **TAUKTAE**, **FANI**, and **FENGAL** maintains optimal scientific coverage across:
- **Basin Balance:** 1 Arabian Sea (TAUKTAE), 2 Bay of Bengal (FANI, FENGAL).
- **Sensor Diversity:** 2 INSAT-3DR (TAUKTAE, FANI), 1 INSAT-3DS (FENGAL).
- **Intensity Diversity:** 2 Extremely Severe Cyclonic Storms (100 kt, 105 kt), 1 Cyclonic Storm (45 kt).

---

## 4. Reconciled Gate D1 Approval Manifest

| Param | Granule 1: TAUKTAE | Granule 2: FANI | Granule 3: FENGAL |
|---|---|---|---|
| **MOSDAC gId** | `9293840` | `7206464` | `14687507` |
| **Filename** | `3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5` | `3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5` | `3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5` |
| **Satellite Platform** | INSAT-3DR | INSAT-3DR | **INSAT-3DS** |
| **Sensor Product** | `3RIMG_L1B_STD` | `3RIMG_L1B_STD` | `3SIMG_L1B_STD` |
| **Nominal Acquisition** | `2021-05-16 23:58 UTC` | `2019-05-02 23:58 UTC` | `2024-11-29 23:30 UTC` |
| **Scene Scan Time** | `2021-05-17 00:00:15 UTC` | `2019-05-03 00:00:20 UTC` | `2024-11-29 23:32:15 UTC` |
| **Synoptic Best-Track Time** | `2021-05-17 00:00:00 UTC` | `2019-05-03 00:00:00 UTC` | `2024-11-30 00:00:00 UTC` |
| **Scan Temporal Delta** | $+2.0\text{ min}$ | $+2.0\text{ min}$ | $-27.75\text{ min}$ |
| **Corrected Latitude** | **`18.50°N`** | **`19.10°N`** | **`12.20°N`** |
| **Corrected Longitude** | **`71.50°E`** | **`85.50°E`** | **`81.20°E`** |
| **IMD Wind Speed** | `100.0 kt` (3-min) | `105.0 kt` (3-min) | `45.0 kt` (3-min) |
| **IMD Central Pressure** | `950.0 hPa` | **`945.0 hPa`** | **`996.0 hPa`** |
| **IMD Category** | ESCS | ESCS | CS |
| **JTWC Wind Speed** | `120.0 kt` (1-min) | `135.0 kt` (1-min) | `45.0 kt` (1-min) |
| **JTWC Pressure** | `931.0 hPa` | `918.0 hPa` | `992.0 hPa` |
| **Basin** | **Arabian Sea** | Bay of Bengal | Bay of Bengal |
| **Reported File Size** | 299,000,000 bytes | 298,000,000 bytes | 281,000,000 bytes |
| **Batch Network Ceiling** | $\le 1,000,000,000$ bytes (Combined batch transfer: ~878,000,000 bytes, Headroom: ~122,000,000 bytes) | | |

---

## 5. Preflight Verification Status

- **Automated Tests:** 114 passed out of 114 tests (`pytest -q`).
- **Linter & Formatter:** Clean, 180 files formatted with zero violations (`ruff check .`, `ruff format --check .`).
- **Historical Invariants:** 1,860 storms, 104,374 observations, frozen SHA-256 `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`.
- **Existing Authentic Corpus:** 4 authentic granules, 4 authentic crops verified on disk.
- **Acquisition State:** Strictly 0 bytes downloaded in this session; waiting for explicit user confirmation.

