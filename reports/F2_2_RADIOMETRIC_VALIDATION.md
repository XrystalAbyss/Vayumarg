# Vayumarg — Milestone F2.2 Radiometric Calibration Validation Report

**Date:** 01 November 2026  
**Status:** VALIDATED & SCIENTIFICALLY VERIFIED  
**Author:** Principal Satellite Remote-Sensing Engineer & Meteorological Research Scientist  
**Milestone:** F2.2 (Multi-Channel INSAT Validation)

---

## 1. Scope & Objective

This report documents the rigorous radiometric calibration validation conducted on the authentic INSAT-3DR Level-1B standard full-disk granule (`3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`, 280.64 MB). The investigation specifically addresses:
1. Exact conversion mechanics from 10-bit raw digital counts to physical brightness temperature ($K$).
2. Analysis of the calibration lookup table (LUT) saturation boundaries and space fill values.
3. Rigorous scientific determination of whether the observed minimum brightness temperature ($179.86\text{ K}$) represents a physical convective overshooting top or a sensor calibration table clamping floor.
4. Physical diurnal illumination constraints across shortwave (VIS/SWIR) vs thermal/water-vapour channels.

---

## 2. Sensor Channel Architecture & Calibration Metadata

The INSAT-3DR Imager payload operates six spectral channels. Two thermal channels are central to continuous day-and-night cyclone monitoring:

| Channel Identifier | Central Wavelength ($\mu\text{m}$) | Spatial Resolution (Nadir) | Matrix Dimensions | LUT Dataset | Fill Value | Valid Range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IMG_TIR1** | 10.8 | 4.0 km | $2816 \times 2816$ | `IMG_TIR1_TEMP` (1024,) | 1023 | 0 – 1022 |
| **IMG_WV** | 6.8 | 8.0 km | $1408 \times 1408$ | `IMG_WV_TEMP` (1024,) | 1023 | 0 – 1022 |
| **IMG_TIR2** | 12.0 | 4.0 km | $2816 \times 2816$ | `IMG_TIR2_TEMP` (1024,) | 1023 | 0 – 1022 |
| **IMG_MIR** | 3.9 | 4.0 km | $2816 \times 2816$ | `IMG_MIR_TEMP` (1024,) | 1023 | 0 – 1022 |
| **IMG_VIS** | 0.65 | 1.0 km | $11264 \times 11264$| `IMG_VIS_ALBEDO` (1024,) | 1023 | Solar Albedo |
| **IMG_SWIR**| 1.625 | 1.0 km | $11264 \times 11264$| `IMG_SWIR_ALBEDO` (1024,)| 1023 | Solar Albedo |

---

## 3. Empirical Digital Count & Calibration Table Analysis

### 3.1 Space Fill Values vs Earth Disk Counts
- In `IMG_TIR1`, digital count `1023` represents `_FillValue` (deep space background outside the Earth disk). Space fill accounts for **85.03%** of the full-disk raster ($6,742,886$ out of $7,929,856$ pixels).
- Valid non-fill pixels across the Earth disk occupy digital counts ranging from **454 to 1005**.

### 3.2 Lookup Table (LUT) Behavior (`IMG_TIR1_TEMP`)
The ISRO L1B radiometric calibration uses pre-computed onboard/ground look-up tables mapping 10-bit integer count $c \in [0, 1023]$ directly to effective brightness temperature $T_B\text{ (Kelvin)}$:
- **Upper Temperature Ceiling (Warm boundary):** Counts $0 \le c \le 80$ are clamped at **$340.06\text{ K}$** ($+66.91^\circ\text{C}$).
- **Monotonic Dynamic Range:** For counts $81 \le c \le 920$, the LUT decreases monotonically from $339.92\text{ K}$ down to $180.05\text{ K}$.
- **Lower Temperature Floor (Cold boundary):** For all counts **$c \ge 921$**, the LUT is clamped at **$179.86\text{ K}$** ($-93.29^\circ\text{C}$).
- Specifically:
  $$\text{LUT}[920] = 180.05\text{ K}, \quad \text{LUT}[921] = 179.86\text{ K}, \quad \text{LUT}[922] = 179.86\text{ K}, \dots, \text{LUT}[1022] = 179.86\text{ K}, \quad \text{LUT}[1023] = 179.86\text{ K}$$

### 3.3 Water Vapour Lookup Table (`IMG_WV_TEMP`)
- For counts $c \ge 995$, `IMG_WV_TEMP` is clamped at **$179.69\text{ K}$**.
- Valid dynamic range: $179.69\text{ K}$ to $300.0\text{ K}$.

---

## 4. Scientific Finding: Resolution of the 179.86 K Mystery

During preliminary F2 analysis, the minimum brightness temperature of the REMAL crop was reported as $179.86\text{ K}$. 

**Empirical Scientific Evidence:**
1. The lowest possible value anywhere in the `IMG_TIR1_TEMP` table is identically $179.86\text{ K}$.
2. In the central convective core of Cyclone REMAL, 12 pixels exhibited digital counts between 921 and 953.
3. All such pixels evaluate to exactly $179.86\text{ K}$ because they hit the LUT calibration floor.
4. **Conclusion:** $179.86\text{ K}$ is **NOT** an unclipped, perfectly resolved physical overshooting cloud top. It is the **lower saturation boundary of the ISRO L1B radiometric lookup table**. Convective clouds colder than $-93.29^\circ\text{C}$ cannot be distinguished from $-93.29^\circ\text{C}$ in standard L1B products.
5. In Vayumarg's scientific dataset, these pixels are explicitly tracked using the boolean mask `is_lower_boundary_clamped`.

---

## 5. Storm-Center Physical State at Acquisition Time

Sampling the calibrated imagery at the IMD synoptic center ($21.70^\circ\text{N}, 89.20^\circ\text{E}$):
- **TIR-1 Brightness Temperature:** **$200.45\text{ K}$** ($-72.70^\circ\text{C}$) — characteristic of deep, cold cirrus anvil overcast surrounding the eyewall.
- **WV Brightness Temperature:** **$216.32\text{ K}$** ($-56.83^\circ\text{C}$) — indicating intense upper-tropospheric moist convection and outflow.
- **Minimum Temperature in 800 km Box:** $179.86\text{ K}$ (clamped convective cluster located in the forward right quadrant).

---

## 6. Diurnal Solar Geometry & Multi-Channel Channel Eligibility

The acquisition timestamp is **2024-05-26 18:02:58 UTC** ($23:32:58\text{ IST}$).
- **Sun Elevation Angle over Cyclone REMAL:** **$-46.75^\circ$** (deep astronomical night).
- Solar reflective channels (`IMG_VIS` at 0.65 $\mu\text{m}$ and `IMG_SWIR` at 1.625 $\mu\text{m}$) receive zero reflected solar irradiance. Their physical signal represents sensor noise / dark current, and albedo calculations yield 0.00.
- **Scientific Architecture Rule:** Module A's primary model architecture must rely upon **TIR-1 (10.8 $\mu\text{m}$) and WV (6.8 $\mu\text{m}$)** as primary continuous 24/7 inputs. Visible and SWIR channels must be segregated and designated `DAYTIME_ONLY_OPTIONAL`, guarded by solar zenith angle filters ($\theta_{zenith} < 80^\circ$).

