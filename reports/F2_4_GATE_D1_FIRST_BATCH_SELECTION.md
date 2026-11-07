# Vayumarg F2.4 Gate D1 — First-Batch Scientific Selection & Strategic Justification

**Date:** 2026-11-02  
**Milestone:** F2.4 Gate D1 — Balanced Acquisition Selection & First-Batch Preflight  
**Auditor:** Satellite Remote-Sensing Engineer, Meteorological Scientist, Quality Auditor  
**Selection Scope:** Selection of the 3 Highest-Value Granules for Gate D1 Execution  
**Status:** **BATCH DEFINED & READY FOR OWNER APPROVAL**  

---

## 1. Multi-Objective Selection Architecture

To select the first operational acquisition batch from the 14 candidates, an 8-axis scoring framework was applied (detailed in `reports/F2_4_GATE_D1_CANDIDATE_SCORING.json`).

The selection protocol enforces:
1. **Network Ceiling Compliance:** Combined source size must be strictly $\le 1,000,000,000\text{ bytes}$ (1.0 GB).
2. **Storm SID Independence:** All selected granules must introduce brand new, independent cyclone SIDs.
3. **Basin & Sensor Diversity:** The batch must enhance Arabian Sea representation and introduce a valid primary IMD label on the modern INSAT-3DS platform.
4. **Intensity Span:** The batch must bridge the gap between lower-intensity cyclonic storms ($40-50\text{ kt}$) and high-end extreme events ($>100\text{ kt}$).

---

## 2. Selected Gate D1 Batch Portfolio ($N=3$)

```
+-------------------------------------------------------------------------------------------------------------------------------+
| GRANULE 1: CYCLONE TAUKTAE (2021) — Arabian Sea High-End Extreme Anchor                                                       |
|   Platform & Product: INSAT-3DR IMAGER | 3RIMG_L1B_STD                                                                        |
|   MOSDAC Asset:       gId 9293840 | 3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5 (~299,000,000 bytes)                           |
|   Acquisition Time:   2021-05-16 23:58:00 UTC (Estimated local scan over eye: 2021-05-17 00:00:15 UTC)                        |
|   Synoptic Fix:       2021-05-17 00:00:00 UTC (+2.0 min offset) | Coord: 18.8°N, 71.5°E                                       |
|   Ground Truth:       IMD: 100.0 kt (ESCS, 950 hPa, 3-min) | JTWC: 120.0 kt (Cat 4 eq, 1-min)                                |
|   Scientific Value:   Deep convective open-ocean eye features in the central Arabian Sea prior to Gujarat landfall.           |
+-------------------------------------------------------------------------------------------------------------------------------+
| GRANULE 2: CYCLONE FANI (2019) — Bay of Bengal Extreme Pre-Landfall Benchmark                                                 |
|   Platform & Product: INSAT-3DR IMAGER | 3RIMG_L1B_STD                                                                        |
|   MOSDAC Asset:       gId 7206464 | 3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5 (~298,000,000 bytes)                           |
|   Acquisition Time:   2019-05-02 23:58:00 UTC (Estimated local scan over eye: 2019-05-03 00:00:20 UTC)                        |
|   Synoptic Fix:       2019-05-03 00:00:00 UTC (+2.0 min offset) | Coord: 19.3°N, 85.3°E                                       |
|   Ground Truth:       IMD: 105.0 kt (ESCS, 940 hPa, 3-min) | JTWC: 135.0 kt (Cat 4/5 eq, 1-min)                              |
|   Scientific Value:   Pre-eminent North Indian Ocean super-intensity benchmark captured ~3 hours before catastrophic landfall.|
+-------------------------------------------------------------------------------------------------------------------------------+
| GRANULE 3: CYCLONE FENGAL (2024) — Modern INSAT-3DS Active Cyclonic Storm Anchor                                              |
|   Platform & Product: INSAT-3DS IMAGER | 3SIMG_L1B_STD                                                                        |
|   MOSDAC Asset:       gId 14687507 | 3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5 (~281,000,000 bytes)                          |
|   Acquisition Time:   2024-11-29 23:30:00 UTC (Estimated local scan over center: 2024-11-29 23:32:15 UTC)                     |
|   Synoptic Fix:       2024-11-30 00:00:00 UTC (30.0 min offset) | Coord: 11.8°N, 80.5°E                                       |
|   Ground Truth:       IMD: 45.0 kt (CS, 994 hPa, 3-min) | JTWC: 45.0 kt (1-min)                                              |
|   Scientific Value:   First active cyclonic storm on ISRO's newest 3DS imager with valid primary IMD category/wind labels.    |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Aggregate Batch Budget & Headroom Analysis

| Metric | Target / Ceiling | Selected Batch 1 Aggregate | Margin / Compliance |
|---|---|---|---|
| **Number of Granules** | $\le 3$ granules | **3 granules** | Exact compliance |
| **Combined Payload Size**| $\le 1,000,000,000\text{ bytes}$ (1.0 GB) | **$878,000,000\text{ bytes}$** (~837.3 MB) | **$122,000,000\text{ bytes}$ headroom (12.2%)** |
| **Distinct New Cyclone SIDs** | Maximized | **3 new storm SIDs** (100% distinct) | Zero SID redundancy |
| **Basin Distribution** | Multi-basin required | **1 Arabian Sea, 2 Bay of Bengal** | Balanced regional representation |
| **Sensor Platforms** | Cross-generational | **2 INSAT-3DR, 1 INSAT-3DS** | Sensor diversity verified |
| **Primary IMD Targets** | Verified continuous wind & category | **45 kt (CS), 100 kt (ESCS), 105 kt (ESCS)** | 100% primary label availability |
| **Transfer Concurrency** | Strictly 1 stream at a time | Sequential execution preflighted | Zero socket collision risk |

---

## 4. Execution Readiness & Safety Directives

- **Local Storage:** The local drive `C:` maintains **49.13 GB free**, providing a safety margin ratio $> 55\times$ relative to the 878 MB batch payload.
- **Resilient Acquisition Engine:** Pre-configured with chunked streaming ($256\text{ KB}$), HTTP Range header verification, automatic backoff retry, and atomic `.part` promotion.
- **Strict Stop Directive:** This document constitutes preflight selection only. **No download will execute until the owner explicitly approves `reports/F2_4_GATE_D1_APPROVAL_MANIFEST.json`.**

