# Vayumarg — Milestone F2.2 Geolocation & Scan Timing Audit Report

**Date:** 01 November 2026  
**Status:** AUDITED & SCIENTIFICALLY CONCLUDED  
**Author:** Principal Geospatial Specialist & Meteorological Data Scientist  
**Milestone:** F2.2 (Multi-Channel INSAT Validation)

---

## 1. Executive Summary

Precise spatial and temporal alignment between satellite imagery and synoptic best-track records is critical for cyclone classification and wind estimation. 
This audit investigates two key discrepancies identified during F2.1B:
1. The **1.0 km offset** between the IMD best-track storm center and the extracted INSAT crop center.
2. The **91.9 km offset** observed between IMD and JTWC advisory positions for Cyclone REMAL at 18:00 UTC on 26 May 2024.
3. The effect of **INSAT scan-line sweep duration** on true observation timing versus synoptic reporting timestamps.

---

## 2. Spatial Alignment & Agency Discrepancy Analysis

At the synoptic reporting time **2024-05-26 18:00:00 UTC**, NOAA IBTrACS NI basin provides two authoritative agency fixes for Cyclone REMAL:

| Agency | Reported Latitude | Reported Longitude | Maximum Sustained Wind | Central Pressure |
| :--- | :--- | :--- | :--- | :--- |
| **IMD (RSMC New Delhi - Primary)** | $21.70^\circ\text{N}$ | $89.20^\circ\text{E}$ | 60 kts (3-min mean) | 978 hPa |
| **JTWC (Secondary)** | $22.20^\circ\text{N}$ | $88.50^\circ\text{E}$ | 55 kts (1-min mean) | 981 hPa |

### 2.1 Inter-Agency Discrepancy ($\Delta d = 91.12\text{ km}$)
Using the WGS84 geodesic formula, the distance between the IMD and JTWC reported positions is:
$$\Delta\text{lat} = 0.50^\circ \ (\approx 55.4\text{ km}), \quad \Delta\text{lon} = -0.70^\circ \ (\approx 72.3\text{ km}) \implies \Delta d = 91.12\text{ km}$$

- **Scientific Conclusion:** This is genuine meteorological agency disagreement between RSMC New Delhi (using radar and INSAT imagery) and JTWC (using automated Dvorak techniques and multi-satellite microwave passes).
- **Vayumarg Handling:** In Vayumarg, image crops are **centered strictly on the primary IMD best-track fix**. JTWC fixes are recorded as secondary labels with explicit spatial offset metadata ($\Delta x, \Delta y, \Delta d$), rather than overwriting or duplicating image rasters.

### 2.2 Investigation of the 1.0 km IMD Center Offset
When extracting the crop centered at $(21.70^\circ\text{N}, 89.20^\circ\text{E})$, the nearest discrete pixel center in the pre-computed L1B coordinate lookup table (`Latitude`, `Longitude`) is:
$$\text{Pixel Lat} = 21.7000^\circ\text{N}, \quad \text{Pixel Lon} = 89.2099^\circ\text{E}$$
$$\Delta\text{lat} = 0.0000^\circ, \quad \Delta\text{lon} = +0.0099^\circ \ (\approx 1.03\text{ km})$$

- At 4.0 km nadir resolution, the pixel grid spacing is $\approx 4.0\text{ km}$.
- The maximum distance from any arbitrary continuous geographic coordinate to the center of its enclosing discrete pixel is:
  $$\frac{\sqrt{4.0^2 + 4.0^2}}{2} \approx 2.83\text{ km}$$
- **Scientific Conclusion:** The observed 1.0 km offset is purely a **sub-pixel grid quantization residual** resulting from nearest-neighbor coordinate matching on a 4.0 km raster. It does not represent any tracking error or georeferencing bias.

---

## 3. Imager Scan Duration & Scan-Line Timing Analysis

Satellite imager scan sweeps are not instantaneous snapshots; they sweep from South to North (or North to South) over several minutes.

### 3.1 INSAT-3DR L1B Scan Metadata
- **Full Disk Scan Start Time:** `18:02:58 UTC`
- **Full Disk Scan End Time:** `18:07:16 UTC`
- **Total Duration:** 4 minutes 18 seconds (258 seconds).

### 3.2 Row-by-Row Interpolation to Cyclone REMAL
- The full disk consists of 2,816 scan rows.
- The center of Cyclone REMAL ($21.7^\circ\text{N}$) corresponds to row index $\approx 835$ (scanned roughly $30\%$ into the acquisition).
- **Exact Line Scan Time:**
  $$t_{\text{scan}} = 18:02:58 + (0.30 \times 258\text{ s}) \approx 18:04:15\text{ UTC}$$

### 3.3 Impact on Cyclone Dynamics
- The synoptic track timestamp is `18:00:00 UTC`.
- Time delta between synoptic fix and actual sensor line sweep:
  $$\Delta t = 18:04:15 - 18:00:00 = 4\text{ minutes } 15\text{ seconds } (255\text{ s})$$
- Cyclone REMAL was translating northward at approximately $15\text{ km/h}$ ($4.17\text{ m/s}$).
- In 255 seconds, the storm moved:
  $$\Delta d_{\text{motion}} = 4.17\text{ m/s} \times 255\text{ s} \approx 1.06\text{ km}$$
- **Scientific Conclusion:** A 1.06 km storm translation during the 4-minute scan interval is roughly one-fourth of a 4 km TIR-1 pixel. This temporal offset is within the noise threshold of satellite-derived cyclone center positioning ($15\text{ km}$ to $30\text{ km}$ typical Dvorak uncertainty) and confirms that standard 15-minute / 30-minute matching windows are scientifically sound.

