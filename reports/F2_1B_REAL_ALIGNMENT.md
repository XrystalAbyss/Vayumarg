# VAYUMARG — Milestone F2.1B: Authentic Satellite-Track Alignment and Export Contract Report

**Milestone:** F2.1B — Live MOSDAC Authentication, Exact-Granule Acquisition and Scientific Acceptance  
**Timestamp:** 2026-11-01T20:17:00+05:30  
**Status:** **VERIFIED_COMPLETE**  
**Author:** Principal Geospatial Architect & Module A Integration Engineer  

---

## 1. Executive Summary

Using the authenticated INSAT-3DR HDF5 granule (`3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`), Vayumarg successfully performed its first **authentic, end-to-end spatiotemporal storm alignment** against authoritative NOAA IBTrACS best-track observations for **Severe Cyclonic Storm REMAL** at peak landfall.

The database now houses verified records flagged strictly with `verification_status = 'REAL_VERIFIED'`, and the Module A training data export contract (`export_satellite_paired_dataset`) has been proven to isolate authentic imagery from synthetic fixtures.

---

## 2. Storm Selection & Best-Track Alignment Truth

### 2.1 Storm Identification
- **Canonical Storm Name:** `REMAL`
- **Season Year:** `2024`
- **Authoritative NOAA IBTrACS Storm ID (SID):** `2024145N14087`
- **US DoD / JTWC Identifier:** `IO012024`
- **Internal Database Storm UUID:** `5f6bfefa-71ed-4a57-95c7-7c12ea930b51`

### 2.2 Landfall Ground Truth Fix
- **Observation Time (UTC):** `2024-05-26 18:00:00+00:00`
- **Authoritative Agency:** `IMD` (India Meteorological Department — RSMC New Delhi)
- **Eye Location:** Lat $21.70^\circ\text{N}$, Lon $89.20^\circ\text{E}$ (coastal Bangladesh / West Bengal border)
- **Intensity:** `60.0 knots` (3-minute sustained wind)
- **Central Pressure:** `978.0 hPa`
- **Classification:** `SCS` (Severe Cyclonic Storm)

---

## 3. Sensor Geodetic Extraction & Crop Registration

### 3.1 Pixel Coordinate Matching
- **Target Best-Track Fix:** Lat $21.7000^\circ\text{N}$, Lon $89.2000^\circ\text{E}$
- **Nearest Scaled Geolocation Grid Pixel:** `row=835`, `col=1783`
- **Pixel Center Coordinates:** Lat $21.7000^\circ\text{N}$, Lon $89.2100^\circ\text{E}$
- **Spatial Offset:** Lat $\Delta = 0.0000^\circ$, Lon $\Delta = +0.0100^\circ$ ($\approx 1.0\text{ km}$)
- **Acquisition Timestamp:** `2024-05-26 18:02:00 UTC` ($\Delta t = 2.0\text{ minutes}$)

### 3.2 Crop Extraction & Thermal Characteristics
- **Crop Geometry:** $201 \times 201$ pixels centered on the cyclone vortex ($\approx 804\text{ km} \times 804\text{ km}$ spatial footprint)
- **Channel Extracted:** `TIR-1` (10.8 $\mu m$)
- **Eye Pixel Brightness Temperature:** $200.45\text{ K}$ ($-72.70\text{ }^\circ\text{C}$)
- **Deep Convection Minimum (Cold Cloud Tops):** $179.86\text{ K}$ ($-93.29\text{ }^\circ\text{C}$)
- **Warm Surface Maximum:** $290.24\text{ K}$ ($+17.09\text{ }^\circ\text{C}$)
- **Mean Convective Core Cloud-Top Temperature:** $211.05\text{ K}$ ($-62.10\text{ }^\circ\text{C}$)
- **Storage URI:** `data/processed/satellite/crops/REMAL_20240526_1802_TIR1.h5`
- **Verification Status:** `REAL_VERIFIED`

---

## 4. Spatiotemporal Association Telemetry

`SatelliteTrackAligner` evaluated candidate observations within temporal ($\le 30\text{ min}$) and spatial ($\le 100\text{ km}$) tolerances and persisted the best matches per agency:

| Target Agency | Observation Time (UTC) | Reported Wind | IMD Category | Temporal Offset | Spatial Offset | Association Confidence | Verification Status |
|---|---|---|---|---|---|---|---|
| **IMD** (Primary RSMC) | `2024-05-26 18:00:00` | **60.0 kts** (3-min) | **SCS** | **2.0 min** | **1.0 km** | **0.962** | **REAL_VERIFIED** |
| **JTWC** (US DoD) | `2024-05-26 18:00:00` | **55.0 kts** (1-min) | — | **2.0 min** | **91.9 km** | **0.507** | **REAL_VERIFIED** |

*Note: WMO New Delhi duplicates were automatically segregated and filtered by the aligner.*

---

## 5. Export Contract Verification (`REAL_VERIFIED`)

Querying `export_satellite_paired_dataset` for Cyclone REMAL (`SID: 2024145N14087`) with default `verification_status = 'REAL_VERIFIED'` yields exactly **2 authentic paired records**:

1. **Record 1 (IMD Ground Truth):**
   - Wind: `60.0 knots` (3-minute sustained)
   - Category: `SCS`
   - Confidence: `0.962`
   - Temporal / Spatial Offset: $2.0\text{ min}$ / $1.0\text{ km}$
   - Verification Status: `REAL_VERIFIED`
2. **Record 2 (JTWC Ground Truth):**
   - Wind: `55.0 knots` (1-minute sustained)
   - Confidence: `0.507`
   - Temporal / Spatial Offset: $2.0\text{ min}$ / $91.9\text{ km}$
   - Verification Status: `REAL_VERIFIED`

### Strict Provenance Isolation Guarantee:
- Quarantined synthetic fixtures remain tagged `SYNTHETIC_FIXTURE` (0 records returned under default `REAL_VERIFIED`).
- Training pipelines consuming the default export contract receive 100% authentic, verified ISRO/NOAA pairs.

