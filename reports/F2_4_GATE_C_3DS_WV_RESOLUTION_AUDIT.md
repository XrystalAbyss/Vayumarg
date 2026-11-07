# Milestone F2.4 — INSAT-3DS Water-Vapour Resolution & Cross-Sensor Contract Audit

## Executive Summary

A critical cross-sensor architectural discrepancy was investigated between the earlier INSAT-3DR mission (e.g., Cyclone REMAL) and the newly recovered INSAT-3DS mission (Cyclone DANA).

While the recovered INSAT-3DS HDF5 file presents Water Vapour (`IMG_WV`) with array dimensions of `(1, 2816, 2805)` identical to Thermal Infrared (`IMG_TIR1`), forensic inspection of internal HDF5 attributes, official SAC/MOSDAC product documentation, and radiometric physics confirms that **the native optical instrument resolution of the INSAT-3DS Water Vapour payload remains 8.0 km at nadir**.

The 4.0 km delivered grid is a ground-segment Level 1B co-registration and spatial reconstruction product. To prevent synthetic super-resolution artifacts in downstream ML architectures, Vayumarg explicitly distinguishes between **delivered product grid spacing** and **effective optical resolution**.

---

## 1. Forensic Inspection of INSAT-3DS L1B HDF5 Metadata

Inspecting `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5` reveals:

```
Dataset: IMG_WV
  Shape: (1, 2816, 2805), Dtype: uint16
  Attributes:
    resolution: [8.]
    resolution_unit: b'km'
    coordinates: b'time Latitude Longitude'
    bandwidth: [0.6]  (6.5 - 7.1 microns)
    bits_per_pixel: [10]
    central_wavelength: [6.8841]
    _FillValue: [1023]
```

In contrast, `IMG_TIR1`:

```
Dataset: IMG_TIR1
  Shape: (1, 2816, 2805), Dtype: uint16
  Attributes:
    resolution: [4.]
    resolution_unit: b'km'
    coordinates: b'time Latitude Longitude'
    bandwidth: [1.0]  (10.3 - 11.3 microns)
    central_wavelength: [10.8288]
```

### Key Technical Findings:
1. **The Ground-Segment Mapping:** The ISRO Space Applications Centre (SAC) Level 1B ground processor reconstructs and maps the Water Vapour channel directly onto the primary 4.0 km geolocation grid (`Latitude`, `Longitude`), rather than delivering a sub-sampled $1408 \times 1402$ array as was done in INSAT-3DR.
2. **Metadata Integrity:** The SAC data generation pipeline faithfully recorded `resolution: [8.]` in the HDF5 attribute header, confirming that the physical telescope Instantaneous Field of View (IFOV) for the 6.8 µm band corresponds to 8.0 km footprint sampling at the sub-satellite point.
3. **Absence of Separate WV Geolocation Grids:** In INSAT-3DR, separate datasets `Latitude_WV` and `Longitude_WV` were required. In INSAT-3DS, no `Latitude_WV` exists; all four IR channels share the master $(2816, 2805)$ coordinate matrix.

---

## 2. Comparative Cross-Sensor Matrix: INSAT-3DR vs. INSAT-3DS

| Sensor Parameter | INSAT-3DR (REMAL) | INSAT-3DS (DANA) | Physical / Meteorological Meaning |
| :--- | :---: | :---: | :--- |
| **Sub-Satellite Longitude** | **74.0°E** | **82.0°E** | INSAT-3DS is centered directly over the central Bay of Bengal |
| **WV Dataset Name** | `IMG_WV` | `IMG_WV` | 6.5–7.1 µm upper/mid-tropospheric moisture |
| **WV Native Array Shape** | `(1, 1408, 1402)` | `(1, 2816, 2805)` | INSAT-3DS delivers WV mapped to the standard IR grid |
| **WV Geolocation Datasets** | `Latitude_WV`, `Longitude_WV` | `Latitude`, `Longitude` | INSAT-3DS eliminates separate subsampled grid |
| **WV Optical Instrument IFOV** | **8.0 km** | **8.0 km** | Optical detector resolution is identical on both satellites |
| **WV Delivered Product Spacing** | **8.0 km** | **4.0 km** | INSAT-3DS L1B ground-segment co-registers WV to 4 km |
| **TIR-1 Native Array Shape** | `(1, 2816, 2805)` | `(1, 2816, 2805)` | Identical 4.0 km nominal grid |
| **TIR-1 Optical Instrument IFOV**| **4.0 km** | **4.0 km** | Identical physical detector resolution |
| **Vayumarg Resampling Action** | Bilinear upsampling to 4 km | Native pass-through (none) | No client-side interpolation needed for INSAT-3DS |

---

## 3. Grid Spacing & Geometric Audit

Around the Cyclone DANA observation center ($21.20^\circ\text{N}, 86.40^\circ\text{E}$ at row 844, column 1515):
- $\Delta\text{Latitude}$ per pixel (North-South): $0.0450^\circ \approx 5.00\text{ km}$
- $\Delta\text{Longitude}$ per pixel (East-West): $0.0400^\circ \times \cos(21.2^\circ) \approx 4.14\text{ km}$
- Effective pixel spacing at $21.2^\circ\text{N}$ is approximately $4.5\text{ km} \times 4.5\text{ km}$ due to earth curvature away from the sub-satellite point ($0.0^\circ\text{N}, 82.0^\circ\text{E}$).

### Parallax and Viewing Geometry Note
While INSAT-3DS at $82.0^\circ\text{E}$ is geographically closer in longitude to DANA ($86.4^\circ\text{E}$) than INSAT-3DR at $74.0^\circ\text{E}$, quantitative cloud-top parallax displacement is a 3-dimensional vector function of:
$$\Delta \vec{r}_{\text{parallax}} = h_{\text{cloud}} \cdot \tan(\theta_{\text{view}}) \cdot \hat{u}_{\text{azimuth}}$$
For deep convective cloud tops ($h_{\text{cloud}} \approx 14\text{–}16\text{ km}$), parallax displacement remains $5\text{–}12\text{ km}$ across both platforms. Ground navigation residuals must not be conflated with best-track meteorological center uncertainty ($\pm 25\text{–}50\text{ km}$).

---

## 4. Standard Cross-Sensor Metadata Contract

To ensure strict scientific integrity in Module A ML pipelines, `MultiChannelCropEngine` and `quality_control_flags` persist the following metadata contract:

```json
{
  "sensor_resolution_audit": {
    "TIR-1": {
      "native_instrument_resolution_km": 4.0,
      "delivered_product_grid_spacing_km": 4.0,
      "target_crop_grid_spacing_km": 4.0,
      "effective_resolution_km": 4.0,
      "resampling_method": "native/none",
      "source_documentation": "MOSDAC INSAT-3DS Operational Products V1 & HDF5 IMG_TIR1 metadata"
    },
    "WV": {
      "native_instrument_resolution_km": 8.0,
      "delivered_product_grid_spacing_km": 4.0,
      "target_crop_grid_spacing_km": 4.0,
      "effective_resolution_km": 8.0,
      "resampling_method": "delivered L1B co-registered grid (no additional interpolation)",
      "source_documentation": "MOSDAC INSAT-3DS Operational Products V1 & HDF5 IMG_WV metadata (resolution=8.0km)"
    }
  }
}
```

This contract guarantees that downstream models are alerted that the WV channel does not provide 4 km optical frequency data, while avoiding unnecessary interpolation artifacts.

