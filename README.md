# Vayumarg 3.0 (वायुमार्ग)

**AI/ML Research & Decision-Support System for Tropical Cyclone Classification, Intensity Estimation and Multi-Horizon Track Forecasting**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![PyTorch 2.6](https://img.shields.io/badge/PyTorch-2.6-orange.svg)](https://pytorch.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.x-green.svg)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![Status](https://img.shields.io/badge/Release-v3.0.0--pre--refactor--baseline-purple.svg)](https://github.com/XrystalAbyss/Vayumarg)

---

## 1. Scientific Overview & Objectives

**Vayumarg (वायुमार्ग)** is a science-first artificial intelligence platform engineered for tropical cyclone monitoring, intensity estimation, and multi-horizon track prediction across the **North Indian Ocean (NIO)** basin—encompassing both the Bay of Bengal and the Arabian Sea.

Tropical cyclogenesis in the North Indian Ocean presents unique operational challenges: severe pre- and post-monsoon storms (e.g., FANI, AMPHAN, BIPARJOY, REMAL, DANA) exhibit rapid intensification, asymmetric cloud convection, and intricate land-interaction dynamics. Vayumarg integrates geostationary satellite remote sensing with deep sequential neural networks and spherical kinematic physics to provide transparent, multi-perspective decision support.

The platform is strictly decoupled into two analytical engines:
- **Module A (Satellite Remote Sensing & Vision):** Single-frame deep convolutional intensity regression and spatiotemporal frame extrapolation from geostationary infrared telemetry.
- **Module B (Trajectory & Intensity Forecasting):** Multi-horizon cyclone trajectory prediction (+6h, +12h, +24h) combining spherical geodesic kinematics with recurrent and hybrid residual networks.

---

## 2. Analytical Engine Architecture

```
                                  VAYUMARG ARCHITECTURE
                                  
     [ Satellite Telemetry ]                          [ Historical Tracks ]
   NASA IR / ISRO INSAT-3DR/3DS                        NOAA IBTrACS (1982-2024)
              │                                                  │
              ▼                                                  ▼
     ┌──────────────────┐                               ┌──────────────────┐
     │     MODULE A     │                               │     MODULE B     │
     │ Satellite Vision │                               │ Track Prediction │
     └────────┬─────────┘                               └────────┬─────────┘
              │                                                  │
    ┌─────────┴─────────┐                              ┌─────────┴─────────┐
    ▼                   ▼                              ▼                   ▼
[ ResNet-18 IR ]  [ ConvLSTM-32-64 ]            [ Geodesic Base ]    [ Track GRU ]
 Single-Frame       Spatiotemporal                Great-Circle       Recurrent Kinematic
 Intensity (kt)     Frame Forecast                 Extrapolation      Multi-Horizon (+24h)
                                                       │                   │
                                                       └─────────┬─────────┘
                                                                 ▼
                                                        [ Hybrid Residual ]
                                                         Learned Physics-
                                                         Guided Correction
```

### 2.1. Module A: Satellite Vision & Intensity Regressor
- **Architecture:** `CycloneCNNRegressor` (Modified ResNet-18 backbone with single-channel IR input layer, global adaptive average pooling, and dual Huber regression + 6-class auxiliary category classification heads).
- **Spatiotemporal Forecaster:** `CycloneConvLSTM` (2-layer ConvLSTM with 32 $\rightarrow$ 64 filters and convolutional frame reconstruction decoder).
- **Training Lineage:** Curated subset of the **NASA Tropical Cyclone Wind Estimation Competition** (GOES-16/17 Band 13 @ 10.3 µm, Himawari-8 @ 10.4 µm; 2,500 images across 25 storm IDs; distinct from TCIR).
- **Pre-processing:** Single-channel IR normalized with $\mu = 0.45, \sigma = 0.22$. Input dimensions: $128 \times 128$ for CNN, $64 \times 64$ for ConvLSTM sequences ($T=3$).
- **Reported Benchmark:** 
  - **ResNet-18 IR Single-Frame Regressor:** 10.00 kt MAE (14.26 kt RMSE, Pearson $r = 0.8642$) across 414 held-out test frames from 5 unseen storms (`xtd`, `gme`, `dzw`, `hig`, `qpq`).
  - **ConvLSTM Spatiotemporal Forecaster:** Achieves **+18.35% skill score** over frame persistence in next-frame pixel reconstruction (MSE 0.01084 vs 0.01328) across 399 test sequences. Intensity persistence (1.90 kt MAE) dominates the ConvLSTM intensity head (17.20 kt MAE) because tropical cyclones exhibit gradual short-range intensity evolution, and recurrent downscaling to $64 \times 64$ px blurs eye-wall convective gradients.

### 2.2. Module B: Trajectory & Multi-Horizon Track Forecasting
- **Great-Circle Geodesic Baseline:** Forward-extrapolates storm positions along spherical Earth geodesics based on the instantaneous translational velocity vector over past 6-hour fixes.
- **Recurrent Track GRU:** `VayumargTrackGRU` (2-layer Gated Recurrent Unit, 96 hidden units, and temporal self-attention context pooling).
- **Hybrid Residual Model:** `VayumargHybridTrackModel` (Combines geodesic kinematic baseline displacement with learned bounded MLP residual corrections).
- **Training Lineage:** **NOAA IBTrACS v04r01** North Indian Ocean historical cyclone archive (1982–2024).
- **Input Representation:** 8 history fixes at 3-hourly intervals (spanning an elapsed observation window of 21 hours) with 10 continuous kinematic features (normalized coordinates, relative displacements, translational velocity, bearing sine/cosine, wind speed, 3-hour intensity delta, and progression index). Zero unverified atmospheric proxy inputs.
- **Empirically Verified Benchmarks (IBTrACS NIO, 1,216 test windows across 51 active test storms):**
  - **+6h Horizon:**
    - Stationary Baseline: 97.51 km
    - Pure Track GRU: 42.19 km MAE (36.00 km median, 50.77 km RMSE, 56.73% skill vs stationary)
    - Geodesic Kinematic Baseline: 35.32 km MAE (30.15 km median, 48.24 km RMSE, 63.78% skill vs stationary)
    - Hybrid Forecaster: **33.31 km MAE** (26.93 km median, 44.19 km RMSE, **5.71% skill vs geodesic** [95% CI: 0.88–3.30 km])
  - **+12h Horizon:**
    - Stationary Baseline: 193.84 km
    - Pure Track GRU: 89.77 km MAE (77.50 km median, 105.49 km RMSE, 53.69% skill vs stationary)
    - Geodesic Kinematic Baseline: 78.27 km MAE (66.42 km median, 98.70 km RMSE, 59.62% skill vs stationary)
    - Hybrid Forecaster: **70.62 km MAE** (60.28 km median, 87.45 km RMSE, **9.78% skill vs geodesic** [95% CI: 4.61–10.91 km])
  - **+24h Horizon:**
    - Stationary Baseline: 388.47 km
    - Pure Track GRU: 239.35 km MAE (217.93 km median, 276.14 km RMSE, 38.39% skill vs stationary)
    - Geodesic Kinematic Baseline: 180.49 km MAE (156.74 km median, 218.19 km RMSE, 53.54% skill vs stationary)
    - Hybrid Forecaster: **158.06 km MAE** (138.96 km median, 189.35 km RMSE, **12.43% skill vs geodesic** [95% CI: 15.04–29.76 km])
- **Scientific Significance of Hybrid Architecture:** At the +24h horizon, unconstrained recurrent neural networks (Pure Track GRU) suffer from trajectory drift (239.35 km MAE), performing significantly worse than a simple great-circle geodesic baseline (180.49 km MAE). The Vayumarg Hybrid Residual model anchors predictions to physical geodesic forward kinematics and learns bounded residual corrections, successfully outperforming both pure deep learning and pure physics across all horizons.

---

## 3. Repository Structure

```
vayumarg/
├── src/vayumarg/              # Core Python package
│   ├── api/                   # FastAPI REST backend and server endpoints
│   ├── core/                  # Configuration, hashing, and structured logging
│   ├── database/              # PostgreSQL/PostGIS connection and SQLAlchemy models
│   ├── ingestion/             # NOAA IBTrACS & ISRO MOSDAC ingestion pipelines
│   ├── ml/                    # Machine learning registry and architectures
│   │   ├── registry.py        # Authoritative, read-only model registry
│   │   ├── vision/            # ResNet-18 CNN & ConvLSTM models and inference
│   │   └── track/             # Track GRU & Hybrid Residual models and inference
│   ├── module_a/              # Module A public data contracts
│   ├── module_b/              # Module B geodesic forecasting engine
│   └── satellite/             # INSAT HDF5 crop extraction and preview generation
├── frontend/                  # React 19 + TypeScript + Vite + Tailwind CSS SPA
├── migrations/                # Versioned Alembic database migration scripts
├── scripts/                   # Training pipelines, dataset preparation, and backup tools
│   ├── backup/                # Google Drive backup and verification runbooks
│   └── ml/                    # Model training and evaluation scripts
├── tests/                     # Unit and integration test suites
├── docs/                      # Architectural decision records and methodology
├── reports/v3/                # Scientific audits, verification reports, and registries
├── docker-compose.yml         # Containerized PostgreSQL 15 + PostGIS stack
└── pyproject.toml             # Python project dependencies and build configuration
```

---

## 4. Quick Start & Installation

### Prerequisites
- Python 3.12+ (managed via `uv` or standard `python -m venv`)
- Node.js 20+ & npm (for frontend compilation)
- Docker Desktop with WSL2 (optional, for PostGIS database)

### Step 1: Clone Repository & Create Environment
```powershell
git clone https://github.com/XrystalAbyss/Vayumarg.git
cd Vayumarg

# Initialize Python 3.12 virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install package in editable development mode
pip install --upgrade pip
pip install -e .
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### Step 2: Install Frontend Dependencies & Compile
```powershell
cd frontend
npm install
npm run build
cd ..
```

### Step 3: Run the Application

#### Option A: Offline Demonstration Mode (Zero Database Dependency)
Vayumarg includes an autonomous offline demonstration cache serving landmark North Indian Ocean cyclones (AMPHAN, FANI, BIPARJOY, REMAL):
```powershell
.\start_vayumarg.ps1 -Offline
```
Access the dashboard at `http://localhost:8000`.

#### Option B: Full PostGIS Database Mode
```powershell
# Copy environment template
Copy-Item .env.example .env

# Spin up PostGIS container
docker compose up -d

# Apply schema migrations
alembic upgrade head

# Launch Vayumarg Studio
.\start_vayumarg.ps1
```

---

## 5. Model Checkpoint Preservation & Cloud Restoration

To maintain strict compliance with public repository licensing and prevent repository bloat, large binary model checkpoints (`*.pt`) are **not** stored directly in Git. They are archived in an authenticated, private Google Drive scientific workspace with strict cryptographic verification.

### Authoritative Model Checkpoints

| Model ID | Checkpoint Filename | Architecture | Size | SHA-256 Cryptographic Identity |
| :--- | :--- | :--- | :--- | :--- |
| `satellite_cnn_best` | `satellite_cnn_best.pt` | ResNet18-IR-SingleChannel | 135.43 MB | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` |
| `satellite_convlstm_best` | `satellite_convlstm_best.pt` | CycloneConvLSTM-32-64 | 4.35 MB | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` |
| `track_gru_best` | `track_gru_best.pt` | VayumargTrackGRU | 1.73 MB | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` |
| `track_hybrid_residual_best` | `track_hybrid_residual_best.pt` | VayumargHybridTrackModel | 0.21 MB | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` |

### Automated Checkpoint Restoration
Authorized researchers with access to the private Google Drive root can restore checkpoints using the quarantine verification runbook:
```powershell
.venv\Scripts\python.exe scripts/backup/checkpoint_cloud_backup.py
```
This script downloads checkpoints into an isolated temporary quarantine directory, validates the exact byte count and SHA-256 checksums, and promotes them atomically into `models/vayumarg/`.

> [!NOTE]
> When model checkpoints are absent, the application gracefully operates in baseline-only mode, serving analytical geodesic trajectories, historical IBTrACS records, and authentic INSAT imagery without raising unhandled runtime exceptions.

---

## 6. Testing & Quality Assurance

Vayumarg maintains an extensive test suite covering model contracts, cryptographic validation, and data quality:

```powershell
# Run the complete unit test suite
pytest tests/unit/ -v

# Verify model registry and PyTorch inference compatibility
python scripts/backup/verify_model_compatibility.py
```

---

## 7. License & Provenance Attributions

- **Codebase:** Licensed under the MIT License.
- **Satellite Data:** NASA Tropical Cyclone Wind Estimation Competition (DrivenData / NASA IMPACT) and ISRO MOSDAC INSAT-3DR/3DS open Earth observation records.
- **Historical Cyclone Tracks:** NOAA National Centers for Environmental Information (NCEI) International Best Track Archive for Climate Stewardship (IBTrACS v04r01, U.S. Public Domain).
- **Meteorological Context:** India Meteorological Department (IMD) RSMC New Delhi operational classification guidelines.
