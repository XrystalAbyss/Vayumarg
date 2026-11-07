# Vayumarg — Milestone F2.3 Multi-Sensor Remote Sensing Validation Report

**Date:** 01 November 2026  
**Status:** **AUDITED & VALIDATED**  
**Role:** Principal Satellite Remote-Sensing Engineer & Geospatial Specialist  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Executive Summary

Milestone F2.3 bridges two generations of ISRO geostationary meteorological satellites: **INSAT-3DR** (operational since 2016) and **INSAT-3DS** (launched 17 February 2024, operational meteorological payload). 
This report analyzes sensor-level differences, geometric projection shifts, and radiometric harmonisation standards required to train multi-platform deep learning models without introducing platform bias.

---

## 2. Platform Comparison Matrix

| Platform Parameter | INSAT-3DR | INSAT-3DS | Scientific Harmonisation Impact |
| :--- | :--- | :--- | :--- |
| **Launch Date** | 08 September 2016 | 17 February 2024 | Modernised electronics and cryogenic coolers |
| **Nominal Sub-Satellite Longitude** | **$74.0^\circ\text{E}$** | **$82.0^\circ\text{E}$** | Geometric view zenith angle shift over Bay of Bengal |
| **Primary Imager Payload** | 6-Channel Imager | 6-Channel Imager | Identical band designations and spatial resolutions |
| **TIR-1 Nadir Resolution** | 4.0 km | 4.0 km | Identical sampling grid ($201 \times 201$ for 800 km) |
| **WV Nadir Resolution** | 8.0 km | 8.0 km | Identical sampling grid ($101 \times 101$ native) |
| **GSICS Radiance Offset** | `lab_radiance_add_offset_gsics` | `lab_radiance_add_offset_gsics` | Supported in both HDF5 metadata headers |
| **L1B Standard Product Code** | `3RIMG_L1B_STD` | `3SIMG_L1B_STD` | Formally registered in `satellite_products` table |

---

## 3. Geometric & Viewing Geometry Harmonisation

### 3.1 Sub-Satellite Longitude Shift ($74.0^\circ\text{E} \to 82.0^\circ\text{E}$)
For cyclones in the eastern Bay of Bengal (e.g. Cyclone REMAL at $89.2^\circ\text{E}$):
- **INSAT-3DR ($74.0^\circ\text{E}$):** Viewing zenith angle $\theta_{zenith} \approx 28.5^\circ$.
- **INSAT-3DS ($82.0^\circ\text{E}$):** Viewing zenith angle $\theta_{zenith} \approx 22.3^\circ$.
- **Atmospheric Path Effect:** The smaller zenith angle from INSAT-3DS results in slightly less atmospheric water-vapour absorption path length, resulting in brightness temperature offsets of approximately $0.3\text{ K} - 0.7\text{ K}$ in clear-sky regions. Over dense convective storm cores (optical depth $\tau \gg 10$), the brightness temperature is dominated by the cloud-top emitting layer, minimizing viewing geometry divergence.

### 3.2 Coordinate Lookup Table (LUT) Handling
Both INSAT-3DR and INSAT-3DS Level-1B products supply pre-computed geodetic coordinates (`Latitude`, `Longitude` for 4 km; `Latitude_WV`, `Longitude_WV` for 8 km). 
- `MultiChannelCropEngine` extracts crops by searching nearest continuous geographic coordinates directly within the native coordinate lookup tables, ensuring that orbital parallax and sub-satellite point differences are automatically accounted for without manual trigonometric reprojection.

---

## 4. Radiometric Cross-Validation Protocol

To guarantee that Module A models do not learn platform-specific calibration artifacts:
1. Both sensors use identical 10-bit integer count ranges $[0, 1023]$ and fill value `1023`.
2. Both sensors map to physical Kelvin units via per-scene pre-computed LUT arrays (`IMG_TIR1_TEMP`, `IMG_WV_TEMP`).
3. Model inputs are standardized to physical Brightness Temperature ($K$) rather than raw counts, ensuring that cross-sensor training is grounded in physical thermodynamics.

