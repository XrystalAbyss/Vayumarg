# VAYUMARG Deep Learning Sprint: Complete ML Data Inventory & Provenance Ledger

## 1. Overview & Data Integrity Mandate

Project VAYUMARG adheres to strict scientific authenticity and zero-hallucination standards. All machine learning models developed during the NOOR 2K26 Emergency Deep Learning Sprint are trained, validated, and evaluated on genuine public and institutional meteorological and satellite remote-sensing datasets.

No synthetic tracks, fake satellite imagery, or fabricated evaluation metrics are present anywhere in the codebase.

---

## 2. Master Dataset Inventory

| Dataset Identifier | Domain | Modality | Source Agency / Institution | Primary Storage Path | Size on Disk | Record Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IBTrACS-NI-v04r01** | Track Kinematics | Tabular CSV | NOAA NCEI / WMO / IMD / JTWC | `data/raw/ibtracs_ni_v04r01.csv` | 27.2 MB | 62,885 rows (473 modern storms post-1980) |
| **NASA-TC-Wind-Frames** | Satellite Vision (Static) | 224×224 TIR JPEGs | NASA IMPACT / NOAA GOES-16/17 ABI (11.2 µm) | `data/raw/satellite/nasa_cyclone/images/` | 14.8 MB | 2,500 frames across 25 named cyclones |
| **NASA-TC-Wind-Sequences** | Spatiotemporal Sequences | 64×64 Multi-frame Tensors | NASA IMPACT / NOAA GOES-16/17 ABI | `data/processed/satellite/nasa_cyclone/sequences_manifest.json` | 1.8 MB | 2,425 chronological sequences ($T=3$) |
| **ISRO-INSAT-Authentic-Crops** | Cross-Domain Evaluation | Multichannel HDF5 / NumPy | ISRO MOSDAC / IMD (INSAT-3DR & 3DS) | `data/processed/crops/` & `data/raw/satellite/` | 84.5 MB | 4 authentic crops (AMPHAN, BIPARJOY, REMAL, DANA) |
| **Demo-Storms-Cache** | Operational Demonstration | JSON Time-series | Historical Best Tracks (IBTrACS / IMD) | `data/demo_cache/storms/` | 4.6 MB | 13 curated landmark North Indian Ocean storms |

---

## 3. Detailed Dataset Specifications

### 3.1 IBTrACS North Indian Ocean (IBTrACS-NI-v04r01)
- **Path**: `data/raw/ibtracs_ni_v04r01.csv`
- **Geographic Coverage**: North Indian Ocean (Bay of Bengal `BB` and Arabian Sea `AS`).
- **Temporal Coverage**: 1980–2024 (modern satellite-era best tracks).
- **Sampling Interval**: Standard 3.0-hour synoptic fixes.
- **Filtering**: Storms with $\ge 12$ chronological observations.
- **Features Extracted**:
  - `lat`, `lon`: Coordinates in degrees North and East.
  - `dx_prev`, `dy_prev`: Local displacement in km relative to previous timestep.
  - `speed_kmh`: Translation speed in km/h.
  - `sin(bearing)`, `cos(bearing)`: Track heading angle.
  - `wind_kt`: 1-minute (JTWC) and 3-minute (IMD) wind intensity.
  - `delta_wind`: 3-hour intensity change.
  - `progression_ratio`: Normalized time index $[0, 1]$.
- **Window Extraction**:
  - History window: $T_{in} = 8$ fixes (24 hours).
  - Forecast targets: +6h (+2 fixes), +12h (+4 fixes), +24h (+8 fixes).
  - Total extracted sequence windows: **11,167 windows**.
- **Splitting Strategy**: Storm-disjoint split by storm `SID` (seed 42):
  - Train: 331 storms (8,201 windows)
  - Validation: 70 storms (1,750 windows)
  - Held-out Test: 72 storms (1,216 windows)

---

### 3.2 NASA Tropical Cyclone Wind Benchmark (Frames & Sequences)
- **Path**: `data/raw/satellite/nasa_cyclone/images/` and `data/processed/satellite/nasa_cyclone/`
- **Origin**: NASA Interagency Implementation and Advanced Concepts Team (IMPACT) & NOAA GOES East/West ABI Thermal Infrared (Band 13, 10.3–11.2 µm).
- **Modality**: Clean geostationary single-channel infrared imagery centered on cyclone eye / circulation center.
- **Target Variable**: 1-minute maximum sustained wind speed in knots (NOAA / JTWC convention).
- **Storm-Disjoint Splits (25 Cyclones)**:
  - **Train (15 storms, 1,619 frames / 1,574 sequences)**:
    `psz` (150 kt), `eoi` (125 kt), `kqu` (120 kt), `vxf` (115 kt), `fcr` (105 kt), `ipa` (110 kt), `fna` (95 kt), `xjo` (85 kt), `gic` (80 kt), `ing` (75 kt), `ywf` (70 kt), `vye` (65 kt), `blq` (65 kt), `rml` (45 kt), `ojv` (35 kt).
  - **Validation (5 storms, 467 frames / 452 sequences)**:
    `wsy` (135 kt), `pjj` (105 kt), `bkh` (85 kt), `zny` (75 kt), `woc` (65 kt).
  - **Held-Out Test (5 storms, 414 frames / 399 sequences)**:
    `xtd` (125 kt), `dzw` (115 kt), `hig` (110 kt), `qpq` (95 kt), `gme` (45 kt).

---

### 3.3 Authentic ISRO INSAT-3DR & 3DS Level-1B Crops
- **Path**: `data/raw/satellite/` and `data/processed/crops/`
- **Origin**: ISRO Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC).
- **Instruments**: INSAT-3DR Imager & INSAT-3DS Imager.
- **Channels**: TIR-1 (10.8 µm), TIR-2 (12.0 µm), MIR (3.9 µm), VIS (0.65 µm).
- **Crops Evaluated**:
  1. **Super Cyclonic Storm AMPHAN** (2020-05-18 09:00 UTC, INSAT-3DR, Peak Intensity: 130 kt IMD / 140 kt JTWC).
  2. **Extremely Severe Cyclonic Storm BIPARJOY** (2023-06-11 06:00 UTC, INSAT-3DR, Intensity: 85 kt IMD / 90 kt JTWC).
  3. **Severe Cyclonic Storm REMAL** (2024-05-26 06:00 UTC, INSAT-3DS, Intensity: 60 kt IMD / 65 kt JTWC).
  4. **Cyclonic Storm DANA** (2024-10-25 09:00 UTC, INSAT-3DS, Post-landfall remnant: JTWC 20 kt, IMD tracking ceased).

---

## 4. Verification Checksum Manifest

All model checkpoints and datasets are verified against their SHA-256 hashes:

| File | SHA-256 Checksum | Verification Status |
| :--- | :--- | :--- |
| `models/vayumarg/vision/satellite_cnn_best.pt` | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | **VERIFIED** |
| `models/vayumarg/vision/satellite_convlstm_best.pt` | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | **VERIFIED** |
| `models/vayumarg/track_gru_best.pt` | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | **VERIFIED** |
| `data/processed/satellite/nasa_cyclone/sequences_manifest.json` | `5c76db3fe619c62955f2d15d6ad5eeb047248e3cf2e09aeef8fa0fe4177dbb1f` | **VERIFIED** |

