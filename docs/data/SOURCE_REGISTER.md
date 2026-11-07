# Scientific Source Register (Vayumarg)

**Purpose:** Comprehensive register of external meteorological and Earth observation data providers planned for ingestion in Vayumarg.

---

## 1. Primary Cyclone Track & Intensity Providers

### 1.1 India Meteorological Department (IMD / RSMC New Delhi)
- **Institution:** India Meteorological Department, Ministry of Earth Sciences, Govt. of India.
- **Role:** WMO Regional Specialized Meteorological Centre (RSMC) for Tropical Cyclones over the North Indian Ocean.
- **Dataset:** RSMC Best Track Archive & Cyclone Warning Bulletins.
- **Version:** Annual Official Releases (1990 – 2024).
- **Temporal Resolution:** 3-hourly synoptic observations (00, 03, 06, 09, 12, 15, 18, 21 UTC).
- **Physical Conventions:** **3-minute sustained maximum surface winds (knots / km/h)**.
- **Citation:** *India Meteorological Department. (2024). Report on Cyclonic Disturbances over the North Indian Ocean. RSMC New Delhi.*
- **License / Access Policy:** Open Government Data (OGD) Platform India / RSMC Public Dissemination.
- **Status in Vayumarg:** Canonical source for ground-truth IMD intensity labels and operational RSMC benchmarks.

---

### 1.2 Joint Typhoon Warning Center (JTWC)
- **Institution:** U.S. Navy / U.S. Air Force, Pearl Harbor, Hawaii.
- **Dataset:** JTWC Northern Indian Ocean Best Track (ATCF format).
- **Version:** Annual post-analysis best tracks (`bni` / `bio` archives).
- **Temporal Resolution:** 6-hourly standard observations (00, 06, 12, 18 UTC) with supplemental 3-hourly fixes.
- **Physical Conventions:** **1-minute sustained maximum surface winds (knots)**.
- **Citation:** *Joint Typhoon Warning Center. (2024). Annual Tropical Cyclone Reports. Naval Oceanography Portal.*
- **License / Access Policy:** Public Domain (US Government Work).
- **Status in Vayumarg:** High-resolution cross-validation track source. Stored under `averaging_period = '1-min'`.

---

### 1.3 NOAA NCEI International Best Track Archive for Climate Stewardship (IBTrACS)
- **Institution:** National Centers for Environmental Information (NCEI / NOAA).
- **Dataset:** IBTrACS Global Tropical Cyclone Best Track Data (North Indian Ocean subset).
- **Version:** v04r01 (Canonical release).
- **Format:** NetCDF-4 and CSV table manifests.
- **Physical Conventions:** Combines multi-agency agency tracks (IMD, JTWC, BOM, CMA, JMA), preserving each center's native wind metrics in separate columns (`wmo_wind`, `usa_wind`, `newdelhi_wind`).
- **Citation:** *Knapp, K. R., et al. (2018). The International Best Track Archive for Climate Stewardship (IBTrACS): Unifying tropical cyclone best track data. Bulletin of the American Meteorological Society, 91(3), 363-376.*
- **License / Access Policy:** Open Data (NOAA Policy).
- **Status in Vayumarg:** Inter-agency consensus and track geometry reconciliation.

---

## 2. Earth Observation Satellite Providers

### 2.1 ISRO MOSDAC (INSAT-3D & INSAT-3DR)
- **Institution:** Space Applications Centre (SAC), Indian Space Research Organisation (ISRO).
- **Satellites:** INSAT-3D (geostationary at 82°E), INSAT-3DR (geostationary at 74°E).
- **Instruments:** IMAGER (6-channel optical/IR radiometer) and SOUNDER (19-channel atmospheric sounder).
- **Key Channels:**
  - Thermal Infrared 1 (TIR-1, 10.3 – 11.3 $\mu\text{m}$, 4 km resolution)
  - Thermal Infrared 2 (TIR-2, 11.5 – 12.5 $\mu\text{m}$, 4 km resolution)
  - Middle Infrared (MIR, 3.7 – 3.9 $\mu\text{m}$, 4 km resolution)
  - Visible (VIS, 0.55 – 0.75 $\mu\text{m}$, 1 km resolution)
  - Water Vapor (WV, 6.5 – 7.1 $\mu\text{m}$, 8 km resolution)
- **Format:** HDF5 (Hierarchical Data Format 5).
- **Citation:** *MOSDAC / SAC / ISRO. (2024). INSAT-3D and INSAT-3DR Imager Meteorological Data Products.*
- **License / Access Policy:** MOSDAC Open Academic & Research Registration.
- **Status in Vayumarg:** Primary visual and thermal input for Module A current-state estimation.

