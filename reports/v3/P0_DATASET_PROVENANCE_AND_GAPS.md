# VAYUMARG 3.0 — P0 DATASET PROVENANCE AND GAPS

**Audit Date:** 7 November 2026  
**Auditor:** Satellite Remote Sensing Scientist & Scientific Data Engineer  
**Classification:** Scientific Data Provenance & Anomaly Investigation  
**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  

---

## 1. Executive Summary

This audit establishes the physical provenance, spectral characteristics, label conventions, and known limitations of every scientific dataset currently stored on disk in the Vayumarg repository. It resolves historical questions regarding atypical image dimensions and provides a realistic appraisal of the data available for future machine learning development.

---

## 2. Dataset 1 — NASA Tropical Cyclone Wind Estimation Subset

### 2.1 Inventory & File Parameters
- **Location on Disk:** `data/raw/satellite/nasa_cyclone/images/`
- **Physical Count:** Exactly 2,500 JPEG files.
- **Total Physical Size:** 43,991,178 bytes (41.95 MB).
- **Unique SHA-256 Hashes:** 2,500 (zero duplicated file contents).
- **Associated Metadata:** `data/processed/satellite/nasa_cyclone/dataset_manifest.json` (1.43 MB) and `sequences_manifest.json` (1.75 MB).
- **Upstream Origin:** DrivenData / NASA IMPACT Tropical Cyclone Wind Estimation Competition (streamed from Hugging Face `torchgeo/tropical_cyclone`).
- **Basin Distribution:** Basin 0 (North Atlantic), Basin 1 (Eastern Pacific), Basin 2 (Western Pacific).

### 2.2 Forensic Investigation of the 111 Atypical 1093×1093 RGB Images
During hackathon audits, 111 images were flagged as having anomalous dimensions ($1093 \times 1093\text{ px}$) and 3-channel RGB format, while the remaining 2,389 images were single-channel grayscale ($366 \times 366\text{ px}$).

**Forensic Findings:**
1. **Storm Identity:** All 111 atypical images belong to a single cyclone: **`gic`** (Western Pacific, Ocean Basin 2, 70 kt peak intensity). Zero other storms contain this format.
2. **Channel Content:** Pixel-level channel decomposition in Python revealed:
   $$\max_{x,y} |R(x,y) - G(x,y)| = 0, \quad \max_{x,y} |R(x,y) - B(x,y)| = 0$$
   All three RGB channels are mathematically identical. The images are single-channel grayscale brightness temperatures packaged into an uncompressed RGB container.
3. **Origin & Upstream Lineage:** Code inspection of `scripts/ml/acquire_nasa_cyclone_data.py` verified that raw bytes were streamed directly from `nasa_tropical_storm_competition_train_source.tar.gz`. The $1093 \times 1093$ images are **genuine source assets created by NASA/DrivenData during dataset creation from JMA Himawari-8 AHI data**, NOT locally altered or synthetic derivatives.
4. **Metadata Defect:** In `acquire_nasa_cyclone_data.py` (line 171), the acquisition script hardcoded `"width": 366, "height": 366, "channels": 1` into `dataset_manifest.json` for all records without querying Pillow dimensions. Thus, a discrepancy existed between the physical disk reality ($1093 \times 1093\text{ RGB}$) and the manifest text ($366 \times 366\text{ px}$).

### 2.3 Partition Verification
- **Storm-Disjoint Splits:**
  - **Train:** 15 storms, 1,619 frames (`blq`, `eoi`, `fcr`, `fna`, `gic`, `ing`, `ipa`, `kqu`, `ojv`, `psz`, `rml`, `vxf`, `vye`, `xjo`, `ywf`).
  - **Validation:** 5 storms, 467 frames (`bkh`, `pjj`, `woc`, `wsy`, `zny`).
  - **Held-Out Test:** 5 storms, 414 frames (`dzw`, `gme`, `hig`, `qpq`, `xtd`).
  - **Disjoint Invariant:** $\text{Train} \cap \text{Val} = \emptyset, \text{Train} \cap \text{Test} = \emptyset, \text{Val} \cap \text{Test} = \emptyset$.
- **Label Framework:** 1-minute sustained wind speed in knots (NOAA / JTWC convention).

---

## 3. Dataset 2 — ISRO MOSDAC Level-1B Granules & Processed Crops

### 3.1 Raw Granules on Disk (`data/raw/satellite/insat_real/`)
There are 8 physical files totaling 2.02 GB:

| Granule File Name | Sensor | Storm | Timestamp (UTC) | Size | State / Usability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5` | INSAT-3DR | FANI | 2019-05-02 23:58 | 303.9 MB | Complete, uncorrupted |
| `3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5` | INSAT-3DR | AMPHAN | 2020-05-19 23:58 | 302.5 MB | Complete, processed into crop |
| `3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5` | INSAT-3DR | TAUKTAE | 2021-05-16 23:58 | 301.6 MB | Complete, uncorrupted (uncropped) |
| `3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5` | INSAT-3DR | BIPARJOY | 2023-06-12 23:58 | 303.0 MB | Complete, processed into crop |
| `3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5` | INSAT-3DR | REMAL | 2024-05-26 18:02 | 294.3 MB | Complete, processed into crop |
| `3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5.part` | INSAT-3DR | REMAL | 2024-05-27 19:15 | 31.5 MB | **Corrupt / Truncated partial download** |
| `3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5` | INSAT-3DS | DANA | 2024-10-25 23:30 | 275.3 MB | Complete, processed into crop |
| `3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5.part` | INSAT-3DS | FENGAL | 2024-11-29 23:30 | 309.1 MB | **Corrupt / Truncated partial download** |

### 3.2 Authentic Multi-Channel Crops (`data/processed/satellite/crops/`)
Five calibrated HDF5 containers exist, each containing coregistered $201 \times 201$ physical Kelvin arrays ($804 \times 804\text{ km}$ spatial bounding box centered on storm vortex):

1. **`AMPHAN_20200519_2358_MULTICHANNEL.h5`** (1.93 MB): Channels: TIR-1, TIR-2, WV, MIR. IMD Retrospective Target: 95.0 kt (ESCS).
2. **`BIPARJOY_20230612_2358_MULTICHANNEL.h5`** (1.93 MB): Channels: TIR-1, TIR-2, WV, MIR. IMD Retrospective Target: 85.0 kt (VSCS).
3. **`REMAL_20240526_1802_MULTICHANNEL.h5`** (1.93 MB): Channels: TIR-1, TIR-2, WV, MIR. IMD Retrospective Target: 60.0 kt (SCS).
4. **`REMAL_20240526_1802_TIR1.h5`** (0.48 MB): Standalone single-channel benchmark crop.
5. **`DANA_20241025_2330_MULTICHANNEL.h5`** (1.93 MB): Channels: TIR-1, TIR-2, WV, MIR. Satellite: INSAT-3DS.

### 3.3 The DANA Scientific Ineligibility Precedent
Cyclone DANA is explicitly tagged in Vayumarg's registry and database as **`INELIGIBLE`** for primary IMD intensity evaluation:
- At observation time (2024-10-25 23:30 UTC), DANA had completed landfall over Odisha and weakened into a broad overland remnant.
- Official IMD best-track protocol discontinued maritime intensity fixes, reporting a nullified category.
- JTWC provided an experimental advisory of 20 kt.
- **Scientific Significance:** Vayumarg preserved DANA as an authentic radiometry test case while strictly preventing it from contaminating operational intensity evaluation.

---

## 4. Dataset 3 — NOAA IBTrACS v04r01 Historical Archive

### 4.1 File Inventory
- **Path:** `data/raw/ibtracs_ni_v04r01.csv` (27,895,917 bytes, ~26.6 MB).
- **Secondary Artifact:** `data/raw/ibtracs_ni_v04r01.csv.part` (25.5 MB incomplete remnant).
- **Scope:** North Indian Ocean basin (Bay of Bengal and Arabian Sea), covering historical records from 1842 to 2024.
- **Active Storm Cohort (1980–2024):** 473 historical cyclones with complete 3-hourly/6-hourly observation tracks.

### 4.2 Agency Conventions & Coexistence
The IBTrACS file aggregates multi-agency reporting:
- `wmo_wind`: WMO 10-minute sustained wind consensus.
- `usa_wind`: US Navy JTWC 1-minute sustained wind standard.
- `newdelhi_wind`: RSMC New Delhi (IMD) 3-minute sustained wind standard.
- `pres`: Central minimum atmospheric pressure in hectopascals (hPa).
- **Vayumarg Handling:** Ingestion routines in `src/vayumarg/ingestion/ibtracs_parser.py` preserve distinct agency columns without forcing cross-agency overwrites or unscientific scalar conflation.

---

## 5. Critical Dataset Gaps & Research Limitations

The following scientific data gaps currently constrain Vayumarg's operational capability:

1. **INSAT Multi-Temporal Sequences are Absent:**
   - On disk, Vayumarg possesses only **single isolated time snapshots** for each cyclone (e.g., AMPHAN at 23:58 UTC, REMAL at 18:02 UTC).
   - **Gap:** There are zero multi-frame INSAT sequences (e.g., $t-2, t-1, t, t+1$). Consequently, the Spatiotemporal ConvLSTM forecaster **cannot be evaluated on genuine INSAT imagery**; it currently executes only on NASA GOES benchmark sequences.
2. **Total INSAT Cyclone Sample Size is Extremely Small ($N=4$):**
   - The entire authentic INSAT library consists of only 4 processed storms (plus 2 unprocessed full-disk granules for FANI and TAUKTAE).
   - A sample size of $N=4$ cannot train a deep convolutional network from scratch. Any model evaluated on INSAT is necessarily performing zero-shot cross-sensor domain transfer.
3. **Absence of Gridded Environmental & Atmospheric Reanalysis Fields:**
   - Vayumarg's track forecasting models rely entirely on past kinematic coordinate fixes ($\Delta x, \Delta y, v, \theta$).
   - Operational cyclone steering is governed by environmental atmospheric dynamics: 850 hPa vorticity, 200 hPa divergence, 850–200 hPa deep vertical wind shear, and Sea Surface Temperature (SST).
   - Neither ERA5 nor GFS gridded fields currently exist in the repository.
4. **TCIR Dataset Absence:**
   - While adapter code exists in `src/vayumarg/satellite/tcir_adapter.py`, the actual multi-gigabyte Tropical Cyclone Image and Reference (TCIR) HDF5 dataset is not locally present.

