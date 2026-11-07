# Vayumarg — Milestone F2.3 Radiometric Quality Control & Sensor Calibration Report

**Date:** 01 November 2026  
**Status:** **AUDITED & STANDARDIZED**  
**Role:** Principal Satellite Remote-Sensing Engineer & Meteorological Research Scientist  
**Milestone:** F2.3 (Controlled Multi-Storm Satellite Acquisition)

---

## 1. Scope & Radiometric Architecture

This report defines the quality assurance and physical calibration protocols applied across authentic ISRO geostationary Imager data (INSAT-3DR and INSAT-3DS).
The pipeline preserves raw 10-bit digital counts alongside calibrated effective brightness temperatures ($K$), enforcing strict separation between instrumental fill values, calibration table saturation floors, and genuine atmospheric signals.

---

## 2. Sensor Channel Characteristics & Calibration Formulas

INSAT Level-1B Standard (`_STD_`) products supply calibrated Radiance and Brightness Temperature lookup tables (LUTs) pre-computed by ISRO Space Applications Centre (SAC):

| Channel Name | Central Wavelength ($\mu\text{m}$) | Spatial Resolution | Raw Data Type | LUT Dataset Name | Missing/Space Fill | Calibration Saturation Floor |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IMG_TIR1** | 10.785 | 4.0 km | 10-bit `uint16` | `IMG_TIR1_TEMP` (1024,) | `1023` | **$179.86\text{ K}$** ($c \ge 921$) |
| **IMG_WV** | 6.866 | 8.0 km | 10-bit `uint16` | `IMG_WV_TEMP` (1024,) | `1023` | **$179.69\text{ K}$** ($c \ge 995$) |
| **IMG_TIR2** | 12.000 | 4.0 km | 10-bit `uint16` | `IMG_TIR2_TEMP` (1024,) | `1023` | **$179.80\text{ K}$** ($c \ge 920$) |
| **IMG_MIR** | 3.900 | 4.0 km | 10-bit `uint16` | `IMG_MIR_TEMP` (1024,) | `1023` | **$180.00\text{ K}$** ($c \ge 940$) |

### 2.1 Raw Count to Brightness Temperature Mapping
The mapping is evaluated via indexed array lookup:
$$T_B(i, j) = \text{LUT}[\min(c(i, j), 1023)]$$
- The attribute `invert: "true"` indicates that higher digital counts correspond to colder brightness temperatures (inverse radiometric scale typical of thermal meteorological sensors).
- Digital count `1023` is the designated `_FillValue`. In Vayumarg, pixels where $c = 1023$ are masked out before temperature statistics are calculated.

---

## 3. Radiometric Clamping Governance

### 3.1 Clamping Floor vs Overshooting Top
In intense tropical cyclones (e.g. SuCS AMPHAN, SCS REMAL), convective cloud tops routinely penetrate the tropopause into the lower stratosphere, reaching temperatures below $-80^\circ\text{C}$ ($< 193\text{ K}$) and occasionally below $-90^\circ\text{C}$ ($< 183\text{ K}$).
- In INSAT L1B products, the lowest temperature represented in `IMG_TIR1_TEMP` is **$179.86\text{ K}$** ($-93.29^\circ\text{C}$).
- All pixels with count $c \ge 921$ evaluate identically to $179.86\text{ K}$.
- **Quality Protocol:** Vayumarg generates an explicit boolean array `clamped_mask = (counts >= 921) & (counts < 1023)`.
- Downstream loss functions in deep learning models (Module A) must treat clamped pixels as censored values ($T \le 179.86\text{ K}$), rather than exact point measurements.

---

## 4. Multi-Channel Masking Standards

For every extracted storm crop ($201 \times 201$), the radiometric quality suite produces:
1. `valid_mask` (Boolean): Identifies valid Earth pixels where counts $\ne 1023$ and coordinate lat/lon are within geographic bounds.
2. `clamped_mask` (Boolean): Identifies saturated deep convective cores hitting LUT boundaries.
3. `combined_valid_mask` (Boolean): Identifies pixels that are simultaneously valid across all extracted channels (TIR-1, WV, etc.).
4. `qc_flags`: Records the ratio of valid pixels and clamped pixels for automated dataset filtering.

