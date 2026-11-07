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
- **Reported Benchmark:** 10.00 kt MAE on held-out test cyclones (414 frames from 5 unseen storms).

### 2.2. Module B: Trajectory & Multi-Horizon Track Forecasting
- **Great-Circle Geodesic Baseline:** Forward-extrapolates storm positions along spherical Earth geodesics based on the instantaneous translational velocity vector over past 6-hour fixes.
- **Recurrent Track GRU:** `VayumargTrackGRU` (2-layer Gated Recurrent Unit, 96 hidden units, and temporal self-attention context pooling).
- **Hybrid Residual Model:** `VayumargHybridTrackModel` (Combines geodesic kinematic baseline displacement with learned bounded MLP residual corrections).
- **Training Lineage:** **NOAA IBTrACS v04r01** North Indian Ocean historical cyclone archive (1982–2024).
- **Features:** 10 continuous kinematic features (normalized coordinates, relative displacements, translational velocity, bearing sine/cosine, wind speed, and progression index). Zero unverified atmospheric proxy inputs.
- **Reported Benchmark:** Track GRU achieves 42.1 km MAE at +6h, 84.7 km MAE at +12h, and 168.3 km MAE at +24h across held-out test tracks.

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
