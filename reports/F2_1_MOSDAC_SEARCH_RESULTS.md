# F2.1 MOSDAC Satellite Data Search and Inventory Report

**Milestone:** F2.1  
**Date:** 2026-11-01  
**Project:** Vayumarg — Scientific Data Foundation (Team VortexA / SIH 2026 / CV-IP)  
**Query Client:** `vayumarg.ingestion.mosdac_client.MOSDACSearchClient`  
**Endpoint:** `https://mosdac.gov.in/apios/datasets.json` (ISRO Official Public Catalog)  

---

## 1. Executive Summary

Using the unauthenticated official ISRO MOSDAC metadata search API, comprehensive granule queries were performed for two severe cyclonic events in the North Indian Ocean:
1. **Primary Candidate — Cyclone REMAL (Bay of Bengal, May 2024)**
2. **Secondary Candidate — Cyclone DANA (Bay of Bengal, October 2024)**

Both queries succeeded, verifying live catalog availability, record identifiers, exact file naming conventions, and file sizes across INSAT-3DR and INSAT-3DS satellites.

---

## 2. Cyclone REMAL Candidate Inventory (Primary Target)

- **Event:** Severe Cyclonic Storm REMAL (Bay of Bengal landfall near Bangladesh/West Bengal border)
- **Temporal Window:** 2024-05-25 to 2024-05-27
- **Primary Sensor:** INSAT-3DR IMAGER Level-1B Standard (`3RIMG_L1B_STD`)
- **Total Available Granules:** 620
- **Total Product Volume:** ~186.7 GB (Average granule size: ~301 MB)
- **Observation Cadence:** 30 minutes

### Sample Verified Candidate Granules (Peak Landfall Stage):

| Granule Filename | Record ID | Timestamp (UTC) | Cadence / Type |
|:---|:---|:---|:---|
| `3RIMG_27MAY2024_2345_L1B_STD_V01R00.h5` | `13631145` | 2024-05-27 23:45:00 UTC | Standard Scan L1B |
| `3RIMG_27MAY2024_2315_L1B_STD_V01R00.h5` | `13630981` | 2024-05-27 23:15:00 UTC | Standard Scan L1B |
| `3RIMG_27MAY2024_2245_L1B_STD_V01R00.h5` | `13630847` | 2024-05-27 22:45:00 UTC | Standard Scan L1B |
| `3RIMG_27MAY2024_2215_L1B_STD_V01R00.h5` | `13630713` | 2024-05-27 22:15:00 UTC | Standard Scan L1B |
| `3RIMG_27MAY2024_2145_L1B_STD_V01R00.h5` | `13630579` | 2024-05-27 21:45:00 UTC | Standard Scan L1B |

---

## 3. Cyclone DANA Candidate Inventory (Secondary Target)

- **Event:** Severe Cyclonic Storm DANA (Odisha / West Bengal coast)
- **Temporal Window:** 2024-10-23 to 2024-10-25
- **Primary Sensor:** INSAT-3DS IMAGER Level-1B Standard (`3SIMG_L1B_STD`)
- **Total Available Granules:** 528
- **Total Product Volume:** ~148.8 GB (Average granule size: ~282 MB)
- **Observation Cadence:** 15 minutes (or 4-min rapid sector scan)

### Sample Verified Candidate Granules (Landfall Window):

| Granule Filename | Record ID | Timestamp (UTC) | Cadence / Type |
|:---|:---|:---|:---|
| `3SIMG_25OCT2024_2351_L1B_STD_V01R00.h5` | `14514935` | 2024-10-25 23:51:00 UTC | Rapid Scan L1B |
| `3SIMG_25OCT2024_2347_L1B_STD_V01R00.h5` | `14514913` | 2024-10-25 23:47:00 UTC | Rapid Scan L1B |
| `3SIMG_25OCT2024_2343_L1B_STD_V01R00.h5` | `14514833` | 2024-10-25 23:43:00 UTC | Rapid Scan L1B |

---

## 4. Bounded Pilot Acquisition Plan

To respect network constraints and the strict pilot budget ($\le 3$ granules, $< 1.0\text{ GB}$ total download), the following target granule is prioritized for acquisition:

- **Target Granule:** `3RIMG_27MAY2024_2345_L1B_STD_V01R00.h5` (Record ID: `13631145`)
- **Sensor:** INSAT-3DR Imager L1B Standard
- **Expected Size:** ~301 MB
- **Channels:** VIS, SWIR, MIR, WV, TIR-1, TIR-2
- **Matching Storm:** Cyclone REMAL (Bay of Bengal)
- **Destination:** `data/raw/satellite/insat_real/`

