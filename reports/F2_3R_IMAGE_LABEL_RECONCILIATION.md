# Vayumarg — Milestone F2.3R Spatiotemporal & Meteorological Label Reconciliation Report

**Date:** 01 November 2026  
**Status:** **AUDITED, QUALIFIED & RECONCILED**  
**Role:** Principal Meteorological Research Scientist, Geospatial Specialist  
**Milestone:** F2.3R (Authentic Satellite Acquisition Reconciliation)

---

## 1. Executive Summary

This report provides the rigorous meteorological reconciliation of temporal, spatial, and agency-specific label alignments between authentic satellite imagery and NOAA IBTrACS best-track records. 
All scan-timing and storm-translation estimates are properly qualified with explicit uncertainty bounds.

---

## 2. Satellite Acquisition Timing & Uncertainty Hierarchy (Section 7.1)

For the authentic baseline granule `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`, distinct temporal markers exist across the telemetry:

| Timing Marker | Recorded / Derived Value | Scientific Nature | Uncertainty / Tolerance |
| :--- | :--- | :--- | :--- |
| **Granule Filename Timestamp** | `1802` | Nominal scheduled acquisition start | Coarse scheduling tag |
| **Telemetry Start Time** | `2024-05-26T18:02:58 UTC` | Direct instrument telemetry attribute | Measured hardware clock |
| **Telemetry End Time** | `2024-05-26T18:07:16 UTC` | Direct instrument telemetry attribute | Measured hardware clock |
| **Full Scene Midpoint** | `2024-05-26T18:05:07 UTC` | Arithmetic midpoint of sweep | $\pm 129\text{ seconds}$ across scene |
| **Inferred Scan-Row Time** | **`2024-05-26 18:04:15 UTC`** | **Linear scan-row interpolation approximation** | **Qualified approximation: $\pm 30 - 60\text{ s}$** |
| **Product Creation Time** | `2024-05-26T23:40:22 UTC` | Ground-station processing completion | Ground telemetry generation |
| **Synoptic Best-Track Fix**| `2024-05-26T18:00:00 UTC` | RSMC New Delhi synoptic reporting time | Standard 3-hour / 6-hour synoptic bin |

### Explicit Scan-Time Qualification:
The observation timestamp of **18:04:15 UTC** is **NOT a directly measured instrument telemetry timestamp**. It is derived via linear interpolation of the 258-second full-disk mirror sweep over 2,816 scan lines, where Cyclone REMAL's nadir center corresponds to row index $r \approx 835$ ($29.65\%$ of the South-to-North mirror sweep). Actual mirror sweep linearity, acceleration/deceleration at turnaround, and blackbody calibration views introduce an estimated uncertainty of $\pm 30\text{ to } \pm 60\text{ seconds}$.

---

## 3. Storm Motion & Spatial Discrepancy Disambiguation (Section 7.2)

To prevent confusion between distinct physical and numerical phenomena, the spatial offsets are formally disambiguated:

### 3.1 Storm Translational Motion During Scan Sweep ($\Delta d \approx 1.06\text{ km}$)
- **Nature:** Derived kinematic approximation.
- **Calculation:** Between the 18:00:00 UTC synoptic fix and the 18:04:15 UTC scan row ($\Delta t = 255\text{ s}$), Cyclone REMAL was translating northward at approximately $15\text{ km/h}$ ($4.17\text{ m/s}$), derived from consecutive synoptic fixes.
- **Physical Displacement:**
  $$\Delta d = 4.17\text{ m/s} \times 255\text{ s} \approx 1.06\text{ km}$$
- This displacement represents approximately **one-fourth of a 4.0 km TIR-1 pixel** and confirms that scan sweep latency does not introduce macroscopic displacement beyond the pixel grid.

### 3.2 Geolocation Pixel-Grid Quantization Residual ($\Delta d \approx 1.03\text{ km}$)
- **Nature:** Sub-pixel nearest-neighbor discrete grid quantization.
- At continuous target $(21.70^\circ\text{N}, 89.20^\circ\text{E})$, the nearest discrete pixel center in the L1B coordinate lookup table is $(21.7000^\circ\text{N}, 89.2099^\circ\text{E})$.
- The residual ($\Delta\text{lat} = 0.00^\circ, \Delta\text{lon} = +0.01^\circ \approx 1.03\text{ km}$) is purely a consequence of 4.0 km grid discretization.

### 3.3 Inter-Agency Position Disagreement ($\Delta d = 91.12\text{ km}$)
- **Nature:** Real meteorological agency operational discordance.
- IMD best-track center: $21.70^\circ\text{N}, 89.20^\circ\text{E}$.
- JTWC advisory center: $22.20^\circ\text{N}, 88.50^\circ\text{E}$.
- Difference: $\Delta\text{lat} = 0.50^\circ, \Delta\text{lon} = -0.70^\circ \implies \Delta d = 91.12\text{ km}$.
- This difference stems from independent subjective and objective center-fixing methodologies (coastal radar vs automated microwave fixes).

---

## 4. Dual-Agency Label Reconciliation (Section 7.3 & 7.4)

The authentic sample carries both agency labels encapsulated within a single deduplicated sample record:

```json
{
  "crop_file": "REMAL_20240526_1802_MULTICHANNEL.h5",
  "storm_sid": "2024146N2189",
  "storm_canonical_name": "REMAL",
  "center_coordinates": [21.70, 89.21],
  "labels": {
    "primary_imd": {
      "agency": "IMD",
      "wind_speed_kt": 60.0,
      "wind_averaging_minutes": 3,
      "central_pressure_hpa": 978.0,
      "category": "Severe Cyclonic Storm (SCS)",
      "spatial_offset_km": 1.03,
      "temporal_offset_seconds": 178
    },
    "secondary_jtwc": {
      "agency": "JTWC",
      "wind_speed_kt": 55.0,
      "wind_averaging_minutes": 1,
      "central_pressure_hpa": 981.0,
      "category": "Tropical Storm (TS)",
      "spatial_offset_km": 91.9,
      "temporal_offset_seconds": 178
    }
  },
  "provenance_status": "REAL_VERIFIED",
  "model_eligibility": "MODEL_ELIGIBLE"
}
```

- **Independent Sample Count:** Exactly **1 independent sample**.
- Dual agency labels are preserved side-by-side and are **never collapsed into an unconditioned scalar regression target**.

