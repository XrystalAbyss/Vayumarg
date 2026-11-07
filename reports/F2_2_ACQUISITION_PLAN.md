# Vayumarg — Milestone F2.2 Controlled Multi-Storm Acquisition Plan

**Date:** 01 November 2026  
**Status:** **PENDING_USER_APPROVAL**  
**Author:** Principal Satellite Data Engineer & Scientific Software Architect  
**Milestone:** F2.2 (Multi-Storm Controlled Acquisition)

---

## 1. Governance & Execution Notice

> [!IMPORTANT]
> In accordance with Vayumarg milestone constraints, **no automated or unapproved satellite data downloads are performed in this milestone**. 
> This document details the exact, vetted acquisition manifest for 6 representative granules spanning four historical North Indian Ocean cyclones. 
> Execution requires interactive MOSDAC authentication and explicit user trigger via `scripts/mosdac_acquire.py`.

---

## 2. Scientific Selection Rationale

The 6 target granules were selected from the 2,173 authentic MOSDAC catalog candidates cataloged in `reports/F2_2_REAL_ASSET_INVENTORY.json`. They satisfy three core scientific requirements:
1. **Multi-Storm Diversity:** Spans Bay of Bengal (REMAL, DANA, AMPHAN) and the Arabian Sea (BIPARJOY).
2. **Multi-Platform Continuity:** Spans both operational ISRO geostationary meteorological satellites: **INSAT-3DR** (2020–2024) and the newest **INSAT-3DS** (2024–present).
3. **Intensity Dynamic Range:** Captures the full spectrum of tropical cyclone life cycles from Cyclonic Storm (CS, 40 kts) to Super Cyclonic Storm (SuCS, 130 kts).

---

## 3. The 6-Granule Controlled Acquisition Manifest

| # | Storm Name | Satellite | Synoptic Stage | Target UTC Timestamp | MOSDAC Record ID (`gId`) | MOSDAC Identifier | Approx Size |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **REMAL** | INSAT-3DR | Peak / Landfall | 2024-05-27 19:15 UTC | `13629859` | `3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5` | ~301 MB |
| **2** | **DANA** | INSAT-3DS | Peak Intensity | 2024-10-25 23:08 UTC | `14514599` | `3SIMG_25OCT2024_2308_L1B_STD_V01R00.h5` | ~282 MB |
| **3** | **DANA** | INSAT-3DS | Post-Landfall | 2024-10-25 23:30 UTC | `14514765` | `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5` | ~282 MB |
| **4** | **AMPHAN** | INSAT-3DR | Rapid Intensif. | 2020-05-19 23:15 UTC | `8353481` | `3RIMG_19MAY2020_2315_L1B_STD_V01R00.h5` | ~290 MB |
| **5** | **AMPHAN** | INSAT-3DR | Super Cyclone (Peak) | 2020-05-19 23:58 UTC | `8353650` | `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5` | ~290 MB |
| **6** | **BIPARJOY**| INSAT-3DR | Arabian Sea Peak | 2023-06-12 23:58 UTC | `11789302` | `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5` | ~291 MB |

**Total Ingestion Volume:** 6 granules $\approx 1.73\text{ GB}$ (well within the local developer storage envelope).

---

## 4. Execution Workflow

When the project owner authorizes acquisition:
1. Run the existing secure interactive acquisition launcher:
   ```powershell
   .venv\Scripts\python scripts/mosdac_acquire.py
   ```
2. Enter the authorized MOSDAC username and password securely via interactive prompt (passwords are handled exclusively in ephemeral memory and never saved to disk or `.env`).
3. The script retrieves the authentic files directly from MOSDAC into `data/raw/satellite/insat_real/` and verifies their SHA-256 hashes against the MOSDAC server metadata.
4. Extracted multi-channel crops will be produced via `MultiChannelCropEngine` and registered into the PostgreSQL database under `REAL_VERIFIED` provenance status.

