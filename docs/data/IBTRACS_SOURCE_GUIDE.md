# NOAA IBTrACS Source Guide — North Indian Ocean (v04r01)

## 1. Overview and Citation

The **International Best Track Archive for Climate Stewardship (IBTrACS)** project, maintained by the National Oceanic and Atmospheric Administration's National Centers for Environmental Information (**NOAA NCEI**), provides the global authoritative archive of tropical cyclone best tracks.

### Official Citation
> Knapp, K. R., Kruk, M. C., Levinson, D. H., Diamond, H. J., & Neumann, C. J. (2010). The International Best Track Archive for Climate Stewardship (IBTrACS): Unifying tropical cyclone best track data. *Bulletin of the American Meteorological Society*, 91(3), 363–376.  
> Knapp, K. R., et al. (2018). *International Best Track Archive for Climate Stewardship (IBTrACS) Project, Version 4*. NOAA National Centers for Environmental Information. https://doi.org/10.25921/82ty-9e16

### Official Source URLs
- **Primary Basin CSV (North Indian Ocean):**  
  `https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv`
- **Reference NetCDF:**  
  `https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/netcdf/IBTrACS.NI.v04r01.nc`
- **Dataset Documentation:**  
  `https://www.ncei.noaa.gov/products/international-best-track-archive`
- **Column Documentation:**  
  `https://www.ncei.noaa.gov/sites/default/files/2025-09/IBTrACS_v04r01_column_documentation.pdf`

---

## 2. File Format and Header Structure

The NOAA IBTrACS CSV distribution employs a **two-row header structure**:

```csv
SID,SEASON,NUMBER,BASIN,SUBBASIN,NAME,ISO_TIME,NATURE,LAT,LON,WMO_WIND,WMO_PRES,...
,Year, , , , , , ,degrees_north,degrees_east,kts,mb,...
1842298N11080,1842,1,NI,BB,UNNAMED,1842-10-25 03:00:00,NR,10.9,80.3,...
```

1. **Row 1 (Headers):** 174 column identifiers specifying primary track variables, synoptic metadata, and agency-specific observation fields.
2. **Row 2 (Units):** Meteorological measurement units corresponding to each column (`kts` for knots, `mb` for millibars / hPa, `degrees_north` / `degrees_east` for coordinates, etc.). This row is automatically validated and skipped during observation ingestion.
3. **Row 3+ (Data Rows):** Chronological synoptic records, typically at 3-hour or 6-hour synoptic intervals (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC).

---

## 3. Reporting Agencies in North Indian Ocean (NI)

In the North Indian Ocean basin (Arabian Sea and Bay of Bengal), multiple agencies compile post-event best tracks:

| Agency Code | Official Organization | Role in North Indian Ocean | Sustained Wind Standard |
| :--- | :--- | :--- | :--- |
| **`NEWDELHI`** | **India Meteorological Department (IMD)** | Regional Specialized Meteorological Centre (**RSMC New Delhi**), designated by WMO as the official regional authority. | **3-minute sustained** |
| **`USA`** | **Joint Typhoon Warning Center (JTWC)** / US Navy & Air Force | Operational tropical cyclone warning center supporting US national and defense assets. | **1-minute sustained** |
| **`IBTRACS / WMO`** | **WMO Reporting Agency Provenance** | Adopts values from designated regional center (`WMO_AGENCY`). Averaging period depends strictly on `WMO_AGENCY`. | **Dynamic: 3-min (`newdelhi`), 10-min (`tokyo`), 1-min (`hurdat_atl`/`atcf`)** |
| **`TOKYO`** | **Japan Meteorological Agency (JMA)** | Appears for cross-basin tropical storms originating in the Western Pacific that transit into the Bay of Bengal. | **10-minute sustained** |
| **`REUNION`** | **Météo-France La Réunion** | Appears for cross-equatorial systems transiting from South-West Indian Ocean. | **10-minute sustained** |

---

## 4. Sustained Wind Averaging Conventions & WMO Provenance

A core scientific principle of Vayumarg is **strict segregation of wind averaging conventions**:

> [!IMPORTANT]
> Sustained wind speed averages differ fundamentally across meteorological traditions. **Never harmonize or convert between 1-minute, 3-minute, and 10-minute winds without an explicit, approved transformation method.** In Vayumarg, raw agency wind measurements are preserved in their native averaging periods. Furthermore, NOAA IBTrACS explicitly documents that `WMO_WIND` does **not** possess a universal 10-minute averaging convention; its averaging period is dynamically inherited from `WMO_AGENCY`.

1. **IMD Standard (3-minute sustained):**
   - Designated by IMD and WMO Regional Association II (Asia).
   - Peak wind represents the maximum 3-minute sustained surface wind (at standard 10-meter elevation).
   - Governs all official IMD cyclone classifications (`D`, `DD`, `CS`, `SCS`, `VSCS`, `ESCS`, `SuCS`).
   - When `WMO_AGENCY` is `newdelhi` (7,042 observations in NI), the `WMO_WIND` column represents this identical 3-minute sustained measurement.
2. **JTWC Standard (1-minute sustained):**
   - Adopted by JTWC and the US National Hurricane Center (NHC).
   - Peak wind represents the maximum 1-minute sustained surface wind.
   - Typically yields numerical values 10% to 15% higher than 3-minute sustained winds for identical storm intensity.
   - When `WMO_AGENCY` is `hurdat_atl` (242 obs) or `atcf` (1 obs), `WMO_WIND` represents 1-minute sustained wind.
3. **JMA / Tokyo Standard (10-minute sustained):**
   - Standard WMO convention adopted by RSMC Tokyo / JMA.
   - In North Indian Ocean data, applies when `WMO_AGENCY` is `tokyo` (645 observations).
4. **Historical / Unmeasured Wind (`unknown`):**
   - 70,583 observations across agencies record no sustained wind (SQL NULL).
   - These are classified strictly as `unknown` averaging period, never assumed to be 10-minute.

---

## 5. Physical Parameter Validation Ranges

Vayumarg validates every ingested meteorological and geospatial measurement against strict physical boundaries:

- **Latitude:** `[-90.0°, +90.0°]`
- **Longitude:** `[-180.0°, +180.0°]`
- **Maximum Sustained Wind:** `[0.0 kts, 300.0 kts]` (values outside this range flagged as `SUSPECT_OUTLIER`)
- **Central Surface Pressure:** `[800.0 hPa, 1080.0 hPa]` (values outside this range flagged as `SUSPECT_OUTLIER`)
- **Missing Data Handling:** Missing values (`""`, `" "`, `"-999"`, `"NaN"`) are strictly stored as `SQL NULL`, never coerced to `0.0`.

