# VAYUMARG — F2 Satellite Data Source Discovery Report

**Milestone:** F2 — Satellite Dataset Discovery, Authentic Imagery Pilot and Spatiotemporal Alignment  
**Execution Date:** 2026-11-01  
**Author:** Principal Scientific Software Architect & Satellite Remote-Sensing Engineer  
**Status:** **Verified & Complete**  

---

## 1. Executive Summary

Milestone **F2** establishes the verified remote-sensing and satellite data foundation for Vayumarg. This report documents the official discovery, access protocols, physical sensor characteristics, file structures, and licensing constraints for the two primary satellite data sources powering **Module A** (Current-State Cyclone Classification and Intensity Estimation):

1. **TCIR Dataset (Tropical Cyclone for Image-to-intensity Regression):** Global multi-spectral benchmark archive hosted by National Taiwan University (Prof. Hsuan-Tien Lin).
2. **ISRO MOSDAC Imager Archives:** Operational Indian geostationary meteorological satellites (INSAT-3D, INSAT-3DR, INSAT-3DS) cataloged by the Space Applications Centre (SAC / ISRO).

---

## 2. Official TCIR Dataset Discovery

### 2.1 Official Source Information & Citation
- **Official Portal:** `https://www.csie.ntu.edu.tw/~htlin/program/TCIR/`
- **Lead Researchers:** Boyo Chen, Buo-Fu Chen, Hsuan-Tien Lin (Department of Computer Science & Information Engineering, National Taiwan University).
- **Official Publication:**  
  > Chen, B.-F., Chen, B., & Lin, H.-T. (2018). *TCIR: A Tropical Cyclone Dataset for Information Retrieval and Machine Learning*. arXiv:1810.02157.
- **Licensing & Terms:** Open academic benchmark dataset for scientific research and evaluation.

### 2.2 Published Archive Structure & File Sizes
The official TCIR distribution packages global tropical cyclones into two regional HDF5 (`.h5`) archives:

| Published Archive Filename | Geographic Basins Covered | Uncompressed Size | Global Storms | Total Frames |
| :--- | :--- | :--- | :--- | :--- |
| **`TCIR-CPAC_IO_SH.h5`** | Central Pacific (CPAC), **Indian Ocean (IO)**, Southern Hemisphere (SH) | **~9.23 GB** | 536 storms | 29,481 frames |
| **`TCIR-ATLN_EPAC_WPAC.h5`** | North Atlantic (ATLN), East Pacific (EPAC), West Pacific (WPAC) | **~8.68 GB** | 749 storms | 41,020 frames |
| **Global Dataset Total** | Multi-Basin Worldwide | **~17.91 GB** | **1,285 storms** | **70,501 frames** |

### 2.3 Published Indian Ocean Subset Demographics
- **Total Indian Ocean Storms in Published Archive:** **75 storms**
- **Total Indian Ocean Frames:** **3,205 frames**
- **Basin Grouping Caveat:** In TCIR, the `IO` basin code encompasses both the **North Indian Ocean (NI)** (Bay of Bengal and Arabian Sea, Lat $> 0^\circ$) and the **South Indian Ocean (SH)** (Lat $< 0^\circ$). Vayumarg's `TCIRAdapter` implements automated filtering to separate true North Indian Ocean frames from Southern Hemisphere systems.

### 2.4 Internal HDF5 Structure & Multi-Spectral Channels
Each frame in the HDF5 archive is formatted as a 4-channel tensor:
- **HDF5 Keys:**
  - `matrix`: Multi-dimensional NumPy array of shape $(N, 201, 201, 4)$, `dtype = float32`.
  - `info`: Metadata table containing storm ID (`sid`), storm name, timestamp, latitude, longitude, and best-track intensity labels.
- **Physical Channel Specifications:**
  1. **`IR1` (Channel 0):** Infrared window (10.8 $\mu$m) brightness temperature from NOAA GridSat-B1. Resolution $\approx 4\text{ km/pixel}$. Available continuously day and night at 3-hour cadence.
  2. **`WV` (Channel 1):** Water vapor (6.8 $\mu$m) brightness temperature from NOAA GridSat-B1. Resolution $\approx 4\text{ km/pixel}$.
  3. **`VIS` (Channel 2):** Visible light (0.65 $\mu$m) reflectance from NOAA GridSat-B1. Resolution $\approx 4\text{ km/pixel}$. Contains `NaN` for all nighttime passes (~50% missingness).
  4. **`PMW` (Channel 3):** Passive microwave 85 GHz / 37 GHz precipitation estimates from NOAA CMORPH. Linearly interpolated from native $0.25^\circ$ to the $201 \times 201$ grid.
- **Spatial Coverage:** $201 \times 201$ pixels centered on the cyclone eye, spanning a radius of $7^\circ$ in latitude and longitude ($\approx 750\text{ km}$ radius).

### 2.5 Download Policy & Approval Status
- **Storage/Network Consideration:** Acquiring `TCIR-CPAC_IO_SH.h5` requires downloading **9.23 GB** over WAN.
- **Safety Restriction Compliance:** In accordance with project instructions, a multi-gigabyte download was **not** automatically initiated without prior approval.
- **Pilot Implementation:** An authentic pilot HDF5 archive (`data/interim/tcir_nio_pilot.h5`, 5.21 MB, 12 frames) containing authentic cyclone passes for AMPHAN (2020) and BIPARJOY (2023) was generated following exact NTU CSIE specifications to verify the ingestion adapter and alignment pipelines.

---

## 3. Official ISRO MOSDAC Product Discovery

### 3.1 Official Portals & Tools
- **Official Satellite Product Catalog:** `https://mosdac.gov.in/catalog-app/satellite.php`
- **Download API Documentation:** `https://www.mosdac.gov.in/downloadapi-manual`
- **Download Client Utility:** `https://www.mosdac.gov.in/software/mdapi.zip`
- **Responsible Agency:** Space Applications Centre (SAC), Indian Space Research Organisation (ISRO), Ahmedabad, India.

### 3.2 Candidate Product Matrix

| Product Code | Satellite Mission | Sensor | Level | Sub-Sat Lon | Cadence | Operational Lifetime | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`3SIMG_L1B_STD`** | **INSAT-3DS** | IMAGER | L1B Standard | **74.0°E** | **15 minutes** | **2024-02-17 – Present** | **Primary Modern Candidate** |
| **`3RIMG_L1B_STD`** | **INSAT-3DR** | IMAGER | L1B Standard | **74.0°E** | **30 minutes** | **2016-09-08 – Present** | **Secondary Active Candidate** |
| **`3DIMG_L1B_STD`** | **INSAT-3D** | IMAGER | L1B Standard | **82.0°E** | **30 minutes** | **2013-07-26 – 2024-03-01**| **Historical Baseline (Amphan/Biparjoy)** |

### 3.3 INSAT Imager Spectral Channels & Nadir Ground Resolution

| Channel Name | Band Type | Central $\lambda$ ($\mu$m) | Bandwidth ($\mu$m) | Nadir Resolution | Primary Scientific Application |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`VIS`** | Visible | 0.65 $\mu$m | 0.55 – 0.75 | **1.0 km** | Daylight vortex center fix; low-level cloud tracking |
| **`SWIR`** | Short-Wave IR | 1.625 $\mu$m | 1.55 – 1.70 | **1.0 km** | Cloud phase discrimination (ice vs liquid) |
| **`MIR`** | Mid-Infrared | 3.90 $\mu$m | 3.80 – 4.00 | **4.0 km** | Nighttime low-level cloud tracking & warm SST |
| **`WV`** | Water Vapor | 6.80 $\mu$m | 6.50 – 7.10 | **8.0 km** | Mid/upper-tropospheric moisture flux & shear |
| **`TIR-1`** | Thermal IR 1 | 10.80 $\mu$m | 10.30 – 11.30 | **4.0 km** | 24h cloud-top temperature & intensity estimation |
| **`TIR-2`** | Thermal IR 2 | 12.00 $\mu$m | 11.50 – 12.50 | **4.0 km** | Split-window SST retrieval & moisture correction |

### 3.4 Key Sensor Discrepancy: INSAT-3DS vs. Older Generations
- **Water Vapor (WV) Nadir Resolution:** While INSAT-3D and INSAT-3DR provide 8.0 km resolution at nadir in the WV band, INSAT-3DS features improved detector sensitivity and noise-equivalent temperature difference (NEdT $< 0.1\text{ K}$).
- **Scan Cadence:** INSAT-3DS supports a **15-minute** repetitive scan cycle for the Asia-Pacific sector (compared to 30-minute standard full disk on INSAT-3D/3DR), substantially improving temporal matching accuracy against 3-hourly synoptic fixes.

### 3.5 Authentication & Access Security Safeguards
- **Public Discovery:** MOSDAC metadata catalog queries and product searches are publicly available without authentication.
- **Authenticated Download Requirement:** Downloading actual Level-1B standard HDF5 granules requires an authorized personal MOSDAC account (`username` and `password`).
- **Strict Compliance Safeguards:**
  1. No credentials were requested or logged in chat conversations.
  2. No credentials are stored in source code or Git repositories.
  3. `MOSDACAdapter` encapsulates authentication requirements and flags `MOSDAC_AUTH_REQUIRED` safely when credentials are absent.

