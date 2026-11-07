# VAYUMARG — F2 ISRO MOSDAC Product Catalog & Imager Sensor Audit

**Milestone:** F2 — Satellite Dataset Discovery, Authentic Imagery Pilot and Spatiotemporal Alignment  
**Execution Date:** 2026-11-01  
**Author:** Principal Scientific Software Architect & Satellite Remote-Sensing Engineer  
**Status:** **Verified & Complete**  

---

## 1. Executive Summary

This report delivers a rigorous technical audit of the **Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC)** catalog, operated by the Space Applications Centre (SAC / ISRO). It defines the sensor characteristics, radiometric calibration formulations, coordinate navigation grids, and acquisition protocols for integrating authentic Indian geostationary satellite imagery into Vayumarg.

Three candidate satellite imager products were verified:
1. **`3SIMG_L1B_STD` (INSAT-3DS):** Operational from 17 February 2024 to present. Primary candidate for recent high-impact cyclones (REMAL, ASNA, DANA, FENGAL).
2. **`3RIMG_L1B_STD` (INSAT-3DR):** Operational from 8 September 2016 to present. Secondary active asset.
3. **`3DIMG_L1B_STD` (INSAT-3D):** Operational from 26 July 2013 to 1 March 2024. Primary archive for historical benchmarks (AMPHAN, BIPARJOY).

---

## 2. Satellite Mission & Payload Specifications

### 2.1 Orbital & Scan Characteristics

| Metric / Parameter | INSAT-3DS (`3SIMG_L1B_STD`) | INSAT-3DR (`3RIMG_L1B_STD`) | INSAT-3D (`3DIMG_L1B_STD`) |
| :--- | :--- | :--- | :--- |
| **Launch Date** | 17 February 2024 | 8 September 2016 | 26 July 2013 |
| **Sub-Satellite Longitude** | **74.0°E** (Geostationary) | **74.0°E** (Geostationary) | **82.0°E** (Geostationary) |
| **Altitude above Equator**| ~35,786 km | ~35,786 km | ~35,786 km |
| **Full Disk Scan Cadence** | **15 minutes** (Asia-Pacific Sector) | **30 minutes** (Full Disk) | **30 minutes** (Full Disk) |
| **Processing Level** | **Level-1B (L1B)** | **Level-1B (L1B)** | **Level-1B (L1B)** |
| **Format** | HDF5 | HDF5 | HDF5 |
| **Radiometric Correction** | RAD LUT / Gain / Offset applied | RAD LUT / Gain / Offset applied | RAD LUT / Gain / Offset applied |

---

## 3. Imager Spectral Channels & Ground Resolution

The Level-1B standard product distributes 6 spectral channels with variable nadir ground resolutions:

| Channel ID | Spectral Band | Wavelength Range ($\mu$m) | Nadir Resolution | Detector Type | Primary Scientific Function in Vayumarg |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`VIS`** | Visible | 0.55 – 0.75 | **1.0 km** | Silicon photodiode array | 1 km vortex center pin-pointing (Daylight only) |
| **`SWIR`** | Short-Wave IR | 1.55 – 1.70 | **1.0 km** | InGaAs detector | Deep convective cloud-top glaciation detection |
| **`MIR`** | Mid-Infrared | 3.80 – 4.00 | **4.0 km** | InSb detector | Low-level circulation tracking at night |
| **`WV`** | Water Vapor | 6.50 – 7.10 | **8.0 km** | HgCdTe detector | Upper-level divergence & moisture flow analysis |
| **`TIR-1`** | Thermal IR 1 | 10.30 – 11.30 | **4.0 km** | HgCdTe detector | Core primary feature: 24h cloud-top temperature |
| **`TIR-2`** | Thermal IR 2 | 11.50 – 12.50 | **4.0 km** | HgCdTe detector | Split-window atmospheric attenuation correction |

---

## 4. Radiometric Calibration & Temperature Retrieval Formulation

### 4.1 Digital Counts to Spectral Radiance
Raw detector counts ($C$) are converted to calibrated spectral radiance ($L_\lambda$ in $\text{mW}/(\text{m}^2 \cdot \text{sr} \cdot \text{cm}^{-1})$) using the calibration LUT or linear slope ($G$) and intercept ($I$) stored in granule attributes:
$$L_\lambda = G \times C + I$$

### 4.2 Radiance to Effective Brightness Temperature (Planck Inversion)
For infrared channels (MIR, WV, TIR-1, TIR-2), the effective brightness temperature ($T_{\text{eff}}$ in Kelvin) is retrieved via Planck's blackbody radiation formula:
$$T_{\text{eff}} = \frac{c_2 \cdot \nu}{\ln\left(1 + \frac{c_1 \cdot \nu^3}{L_\lambda}\right)}$$

Where:
- $c_1 = 1.191042 \times 10^{-5}\text{ mW} \cdot \text{m}^{-2} \cdot \text{sr}^{-1} \cdot (\text{cm}^{-1})^{-4}$ (First radiation constant)
- $c_2 = 1.4387752\text{ cm} \cdot \text{K}$ (Second radiation constant)
- $\nu = \frac{10^4}{\lambda_{\text{center}}}\text{ cm}^{-1}$ (Central wavenumber, where $\lambda_{\text{center}}$ is in $\mu\text{m}$)

### 4.3 Band Temperature Adjustment
Sensor-specific nonlinear response is corrected to physical temperature ($T$ in Kelvin):
$$T = a + b \cdot T_{\text{eff}}$$
*(Coefficients $a$ and $b$ are published in MOSDAC L1B product header attributes for each scan).*

---

## 5. Candidate Real Storm Alignment Opportunities

Cross-referencing Vayumarg's verified database (`vayumarg`) against MOSDAC operational windows yields the following primary candidates:

| Candidate Storm Name | Season | Basin | Ingested Track Obs | Operational Sensor | Recommended Matching Window |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cyclone DANA** | **2024** | Bay of Bengal | 109 observations | **INSAT-3DS (`3SIMG_L1B_STD`)** | **15 minutes** |
| **Cyclone REMAL** | **2024** | Bay of Bengal | 115 observations | **INSAT-3DS (`3SIMG_L1B_STD`)** | **15 minutes** |
| **Cyclone ASNA** | **2024** | Arabian Sea | 196 observations | **INSAT-3DS (`3SIMG_L1B_STD`)** | **15 minutes** |
| **Cyclone BIPARJOY** | **2023** | Arabian Sea | 316 observations | **INSAT-3D / 3DR** | **30 minutes** |
| **Cyclone AMPHAN** | **2020** | Bay of Bengal | 146 observations | **INSAT-3D / 3DR** | **30 minutes** |

---

## 6. Access Protocol & Authentication Boundary Safeguards

1. **Catalog Search API (Unauthenticated):**
   - Query endpoint: `https://mosdac.gov.in/catalog-app/satellite.php`
   - Parameters: Satellite name, sensor, product code, bounding box, start/end dates.
2. **Granule Download API (Authenticated):**
   - Endpoint: `https://www.mosdac.gov.in/downloadapi`
   - Authentication requirement: HTTP Basic Auth or session token via registered MOSDAC credentials.
3. **Safe Acquisition Protocol:**
   - Operators can register their credentials in a restricted local environment file (`.env.local`, excluded from Git).
   - `MOSDACAdapter` checks credentials dynamically and reports `MOSDAC_AUTH_REQUIRED` safely if credentials are not configured.

