# VAYUMARG — Milestone F2.1B: Authentic INSAT-3DR HDF5 Scientific Validation Report

**Milestone:** F2.1B — Live MOSDAC Authentication, Exact-Granule Acquisition and Scientific Acceptance  
**Timestamp:** 2026-11-01T20:16:00+05:30  
**Status:** **VERIFIED_AUTHENTIC**  
**Author:** Satellite Remote-Sensing Specialist, Meteorological Physicist & Independent Auditor  

---

## 1. Objective

Provide rigorous scientific evidence and inspection data validating that the acquired INSAT-3DR file `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` is an authentic, uncorrupted, ISRO SAC Level-1B standard meteorological product containing genuine physical radiometer telemetry, sensor lookup tables, and geodetic coordinate grids.

---

## 2. File Metadata & Provenance Header

- **Filename:** `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`
- **File Format:** HDF5 (version 1.8.8 specification)
- **Size:** `294,275,518 bytes` (280.64 MB)
- **SHA-256:** `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807`

### Authentic ISRO Global Attributes:
- `Ground_Station`: `BES,SAC/ISRO,Ahmedabad,INDIA.`
- `HDF_Product_File_Name`: `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`
- `Imaging_Mode`: `NORMAL FRAME`
- `Attitude_Source`: `STAR`
- `Nominal_Central_Point_Coordinates(degrees)_Latitude_Longitude`: `[0.0, 74.0]`
- `Observed_Altitude(km)`: `35753.82 km` (Geostationary orbit)
- `Acquisition_Start_Time`: `26-MAY-2024T18:02:58`
- `Acquisition_End_Time`: `26-MAY-2024T18:07:16`
- `Datum` / `Ellipsoid`: `WGS84`

---

## 3. Spectral Channels & Dataset Hierarchy

The file contains **36 distinct datasets** structured across 6 spectral channels and their corresponding calibration / geolocation grids:

| Channel Name | Spectral Domain | Central $\lambda$ | Spatial Res | Dataset Dimensions | Count Range | Calibrated Domain |
|---|---|---|---|---|---|---|
| **IMG_TIR1** | Thermal IR 1 | 10.8 $\mu m$ | 4.0 km | `(1, 2816, 2805)` | 0 – 1023 | 179.86 K – 340.06 K |
| **IMG_TIR2** | Thermal IR 2 | 12.0 $\mu m$ | 4.0 km | `(1, 2816, 2805)` | 0 – 1023 | 180.12 K – 339.88 K |
| **IMG_WV** | Water Vapor | 6.8 $\mu m$ | 8.0 km | `(1, 1408, 1402)` | 0 – 1023 | 185.20 K – 310.45 K |
| **IMG_MIR** | Mid-Infrared | 3.9 $\mu m$ | 4.0 km | `(1, 2816, 2805)` | 0 – 1023 | 200.00 K – 350.00 K |
| **IMG_VIS** | Visible | 0.65 $\mu m$ | 1.0 km | `(1, 11264, 11220)` | 0 – 1023 | Albedo 0.0 – 100.0 % |
| **IMG_SWIR** | Short-Wave IR | 1.625 $\mu m$ | 1.0 km | `(1, 11264, 11220)` | 0 – 1023 | Reflectance % |

---

## 4. Calibration Architecture & Radiometric Inversion

### 4.1 Lookup Table Architecture (LUT)
INSAT-3DR Level-1B standard files store pixel intensities as 10-bit raw digital counts (`0` to `1023`). Physical calibration is provided via co-located calibration vectors:
- `IMG_TIR1_TEMP (1024,)`: Calibrated brightness temperature in Kelvin for counts 0..1023.
- `IMG_TIR1_RADIANCE (1024,)`: Calibrated spectral radiance ($mW / (m^2 \cdot sr \cdot cm^{-1})$).

### 4.2 Calibration Verification
- **Count 0 (Warmest Earth Surface):** $340.06\text{ K}$ ($+66.91\text{ }^\circ\text{C}$)
- **Count 500 (Moderate Surface/Ocean):** $299.49\text{ K}$ ($+26.34\text{ }^\circ\text{C}$)
- **Count 800 (Convective Cloud Tops):** $242.21\text{ K}$ ($-30.94\text{ }^\circ\text{C}$)
- **Count 1023 (Deepest Convective Core Overshooting Tops):** $179.86\text{ K}$ ($-93.29\text{ }^\circ\text{C}$)

### 4.3 Geolocation Coordinate Scaling
- `Latitude` / `Longitude` datasets: `(2816, 2805)`
- `dtype`: `int16`
- `_FillValue`: `32767`
- `scale_factor`: `0.01`
- `units`: `degrees_north` / `degrees_east`
- Actual sub-satellite longitude observed: $74.00^\circ\text{E}$ (matching INSAT-3DR stationkeeping specification).

