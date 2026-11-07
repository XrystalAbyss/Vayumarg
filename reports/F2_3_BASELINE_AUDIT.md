# Vayumarg — Milestone F2.3 Baseline Audit & Preprocessing Verification Report

**Date:** 01 November 2026  
**Status:** **AUDITED, INDEPENDENTLY RECALCULATED & VERIFIED**  
**Role:** Principal Scientific Data Architect, Satellite Remote-Sensing Engineer, Meteorological Research Scientist  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Executive Summary

Prior to initiating multi-granule acquisition and catalog reconciliation under Milestone F2.3, an independent verification of all F2.2 scientific baseline claims was conducted. Every cryptographic asset hash, database identity invariant, and radiometric metric was recomputed directly from the authentic raw assets and production database.

---

## 2. Cryptographic Asset & Baseline Verification

The physical files on disk and the database foundation were inspected:

| Baseline Asset | Path | Expected SHA-256 | Recomputed SHA-256 | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Authentic INSAT-3DR Raw Granule** | `data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | `5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807` | **MATCH (BIT-PERFECT)** |
| **Multi-Channel Processed Crop** | `data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5` | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | `7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90` | **MATCH (BIT-PERFECT)** |
| **Frozen Historical Dataset Manifest** | `data/manifests/vayumarg_f1_1_freeze_manifest.json` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107` | **MATCH (BIT-PERFECT)** |

- **Drive Capacity:** 49.9 GB available on drive `C:`, providing ample headroom for bounded acquisitions (< 2.0 GB).
- **PostgreSQL / PostGIS Database:** Verified operational with 1,860 storms, 104,374 observations, 10 registered satellite products, 2 granules (1 REAL_VERIFIED, 1 SYNTHETIC_PILOT), 13 crops (1 REAL_VERIFIED, 12 SYNTHETIC_PILOT), and 23 associations (2 REAL_VERIFIED, 21 SYNTHETIC_PILOT).
- **Alembic Version:** `006_satellite_provenance (head)` applied.

---

## 3. Independent Recalculation of F2.2 Scientific Claims

### B1. TIR-1 Fill-Mask Integrity Audit
The raw array shape and space fill values were recalculated directly from `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`:
- **Raw Array Shape:** `(1, 2816, 2805)` $\implies 7,898,880$ total pixels.
- **Fill Attribute:** `IMG_TIR1.attrs['_FillValue'] = 1023` (`uint16`).
- **Full Disk Space Fill Count:** Exactly `6,716,047` pixels (**85.03%** of array).
- **Valid Earth Pixels:** Exactly `1,182,833` pixels (**14.97%** of array).
- **Geographic Footprint:**
  - Latitude: $-81.04^\circ\text{S}$ to $+81.04^\circ\text{N}$
  - Longitude: $-7.15^\circ\text{W}$ to $+155.15^\circ\text{E}$
- **Remal Crop (201x201 = 40,401 pixels):**
  - Valid Pixels: 40,000 (**99.01%**)
  - Invalid (Edge / Missing) Pixels: 401 (**0.99%**)

### B2. Lower-Temperature LUT Clamping Audit
- **LUT Clamping Floor:** `IMG_TIR1_TEMP` lookup table clamps all counts $c \ge 921$ to **$179.86\text{ K}$**.
- **Full Disk Earth Clamping:** Out of 1,182,833 valid Earth pixels, **17,735 pixels** ($1.4994\%$) exhibit digital counts in $[921, 1022]$.
- **Remal Crop Clamping:** Out of 40,000 valid pixels in the storm bounding box, **8,472 pixels** ($21.18\%$) exhibit counts $\ge 921$.
- **Scientific Implication:** More than 21% of the central dense overcast (CDO) of Cyclone REMAL is at or below the $179.86\text{ K}$ ($-93.29^\circ\text{C}$) calibration boundary. In Vayumarg, these pixels are explicitly tracked using an independent boolean mask (`native/TIR-1/clamped_mask`), preventing unphysical temperature modeling.

### B3. Scan Timing Reconstruction & Uncertainty
- **Direct Instrument Metadata:**
  - `Acquisition_Start_Time`: `26-MAY-2024T18:02:58`
  - `Acquisition_End_Time`: `26-MAY-2024T18:07:16`
  - Scene sweep duration: **258 seconds** (4 minutes 18 seconds).
- **Reconstruction Method:** The row observation time of **18:04:15 UTC** is a **documented linear interpolation reconstruction** based on Cyclone REMAL's nadir scan row index ($r = 835$ of 2,816 total rows, corresponding to $29.65\%$ of the South-to-North mirror sweep):
  $$t_{\text{scan}} = 18:02:58 + (0.2965 \times 258\text{ s}) = 18:04:15\text{ UTC}$$
- **Timing Uncertainty:** Estimated at $\pm 30\text{ seconds}$ due to mirror deceleration, calibration blackbody view, and turn-around periods.
- **Storm Translation Displacement:** Between the synoptic best-track timestamp (`18:00:00 UTC`) and the line scan (`18:04:15 UTC`, $\Delta t = 255\text{ s}$), Cyclone REMAL was translating northward at $\approx 15\text{ km/h}$ ($4.17\text{ m/s}$). The physical displacement is:
  $$\Delta d = 4.17\text{ m/s} \times 255\text{ s} \approx 1.06\text{ km}$$
  This is approximately one-fourth of a 4.0 km TIR-1 pixel and represents sub-pixel displacement.

### B4. Water-Vapour Normalized Bilinear Resampling Audit
- The implementation of `bilinear_resample_2d` in `src/vayumarg/satellite/crop_engine.py` was audited and upgraded:
  - Supports normalized bilinear interpolation when a `valid_mask` is supplied or when NaNs are present:
    $$res = \frac{\sum w_i m_i v_i}{\sum w_i m_i}$$
  - Guarantees invalid values (space fill or 999 K) cannot contaminate adjacent valid pixels.
  - Where all neighbors are invalid, the output evaluates strictly to `np.nan` and is **never silently substituted with 0.0 K**.
- Regression tests added in `tests/unit/test_multichannel_crop_engine.py`:
  - `test_bilinear_resample_with_valid_mask_prevents_contamination`: PASSED
  - `test_bilinear_resample_nan_propagation_and_no_zero_substitution`: PASSED

