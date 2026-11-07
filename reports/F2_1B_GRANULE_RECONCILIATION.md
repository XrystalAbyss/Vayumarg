# F2_1B Granule Reconciliation and API Semantics Report

**Milestone:** F2.1B  
**Date:** 2026-11-01  
**Project:** Vayumarg — Scientific Data Foundation (Team VortexA / SIH 2026 / CV-IP)  
**Auditor:** Principal Satellite Remote-Sensing Specialist & API Architect  

---

## 1. Executive Summary & Forensic Findings

In Milestone F2.1A, an initial search reported 620 candidate granules for Cyclone REMAL and 528 for Cyclone DANA across multi-day windows.
An independent verification of ISRO MOSDAC's Search API (`https://mosdac.gov.in/apios/datasets.json`) was executed to reconcile those counts and establish the exact semantics of MOSDAC query parameters.

### Key Discoveries:
1. **Granule-Level vs Product-Level Records:**
   The endpoint `/apios/datasets.json` returns granular acquisition metadata (`entries`), including unique numerical record IDs (`id`), standard HDF5 identifiers (`identifier`), and product timestamps (`updated`).
2. **Temporal Cadence during Cyclones:**
   During Severe Cyclonic Storm REMAL (26 May 2024), INSAT-3DR operated in a high-cadence rapid-scan mode (~4–5 minute interval) rather than a fixed 30-minute schedule. For 26 May 2024 alone, exactly **288 granules** (~83.7 GB) were generated.
3. **Exact Semantics of `gId`:**
   - When `gId` is queried with the **numerical record identifier** (e.g., `gId="13623453"`), MOSDAC returns HTTP 200 with `totalResults: 1`, isolating that precise granule.
   - When `gId` is queried with the alphanumeric `.h5` filename, MOSDAC returns HTTP 400 (Validation Error).
   - Therefore, Vayumarg's exact granule selector must map either numerical IDs directly to `gId`, or accept filenames and resolve them to their corresponding numerical record ID before calling `mdapi.py`.

---

## 2. Cyclone REMAL Timing Correction (Phase B)

The previous preliminary report proposed `3RIMG_27MAY2024_2345_L1B_STD_V01R00.h5`, which was post-landfall (27 May 23:45 UTC).
Official India Meteorological Department (IMD) cyclone bulletins place REMAL's coastal crossing across Bangladesh and adjoining West Bengal coasts between **17:00 and 19:00 UTC on 26 May 2024**.

In the Vayumarg database, Canonical Storm REMAL has authoritative IBTrACS SID `2024145N14087` (US DoD / JTWC `IO012024`).

### Verified Landfall Window Candidates (26 May 2024):

| Stage | Observation Time (UTC) | IMD Intensity & Category | MOSDAC Granule Identifier | Record ID (`gId`) | Time Offset |
|:---|:---|:---|:---|:---|:---|
| **Pre-Landfall** | 2024-05-26 15:00:00 | 60 kts (3-min), SCS (978 hPa) | `3RIMG_26MAY2024_1502_L1B_STD_V01R00.h5` | `13622691` | +2 min |
| **Eye Approach** | 2024-05-26 17:00:00 | 60 kts (3-min), SCS (978 hPa) | `3RIMG_26MAY2024_1702_L1B_STD_V01R00.h5` | `13623211` | +2 min |
| **Peak Landfall (Primary)** | 2024-05-26 18:00:00 | 60 kts (3-min), SCS (978 hPa) | `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` | `13623453` | +2 min |
| **Post-Landfall** | 2024-05-26 21:00:00 | 55 kts (3-min), SCS (980 hPa) | `3RIMG_26MAY2024_2102_L1B_STD_V01R00.h5` | `13624421` | +2 min |

---

## 3. Targeted Single Granule Selection

The chosen primary pilot granule for authentic acquisition is:
- **Product:** `3RIMG_L1B_STD` (INSAT-3DR Imager L1B Standard)
- **Granule Identifier:** `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`
- **Numerical Record ID (`gId`):** `13623453`
- **Timestamp:** 2024-05-26 18:02:00 UTC (2 minutes after synoptic observation 18:00 UTC)
- **Storm Coordinates:** 21.70°N, 89.20°E
- **Estimated File Size:** ~290.8 MB (Strictly within the $\le 1000\text{ MB}$ pilot budget)

