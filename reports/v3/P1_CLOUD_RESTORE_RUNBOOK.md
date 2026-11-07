# VAYUMARG 3.0 — P1 CLOUD DISASTER RECOVERY & WORKSTATION RESTORATION RUNBOOK

**Document Version:** 1.0.0  
**Date:** 7 November 2026  
**Auditor:** Systems Integration Engineer & Research Reproducibility Auditor  
**Scope:** Clean Windows Workstation Disaster Recovery from GitHub & Google Drive  

---

## 1. Overview & Recovery Objectives

This runbook specifies the complete, deterministic procedure to reconstruct the Vayumarg 3.0 scientific environment from scratch on a clean Windows 11 workstation using:
1. **Source Code & Manifests:** Cloned from canonical GitHub repository (`https://github.com/XrystalAbyss/Vayumarg`).
2. **Binary Models & Datasets:** Restored from the private, restricted Google Drive folder (`18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth`).

---

## 2. Step-by-Step Workstation Reconstruction Procedure

### Step 1: Clone Source Repository from GitHub
```powershell
git clone https://github.com/XrystalAbyss/Vayumarg.git C:\Users\astra\Desktop\Project\Vayumarg
cd C:\Users\astra\Desktop\Project\Vayumarg
git checkout main
```

### Step 2: Restore Model Checkpoints from Google Drive
From Drive folder `03_Trained_Models/`, download the four verified checkpoints into `models/vayumarg/`:
- `models/vayumarg/vision/satellite_cnn_best.pt` (129.16 MB)
- `models/vayumarg/vision/satellite_convlstm_best.pt` (4.15 MB)
- `models/vayumarg/track_gru_best.pt` (1.65 MB)
- `models/vayumarg/track_hybrid_residual_best.pt` (0.20 MB)

### Step 3: Restore Calibrated Satellite Crops & Datasets
From Drive folder `02_Scientific_Datasets/`, download:
- `data/processed/satellite/crops/*.h5` (5 multi-channel HDF5 crops)
- `data/raw/ibtracs_ni_v04r01.csv` (NOAA historical track archive)
- `data/raw/satellite/nasa_cyclone/images/*.jpg` (2,500 training images)

### Step 4: Cryptographic Checksum Validation
Execute the automated checksum validator to confirm bitwise parity before executing any code:
```powershell
.venv\Scripts\python.exe -c "
import hashlib
from pathlib import Path

expected = {
    'models/vayumarg/vision/satellite_cnn_best.pt': '2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865',
    'models/vayumarg/vision/satellite_convlstm_best.pt': '007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d',
    'models/vayumarg/track_gru_best.pt': '24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986',
    'models/vayumarg/track_hybrid_residual_best.pt': '7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0',
}

for path_str, exp_hash in expected.items():
    p = Path(path_str)
    assert p.exists(), f'Missing file: {path_str}'
    act_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    assert act_hash == exp_hash, f'Checksum mismatch for {path_str}!'
    print(f'[OK] Verified {path_str}')
print('All model checkpoints verified successfully.')
"
```

### Step 5: Recreate Python Virtual Environment
```powershell
# Create Python 3.12 virtual environment
python -m venv .venv

# Activate environment and install dependencies
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### Step 6: Install Frontend Dependencies & Compile Bundle
```powershell
cd frontend
npm install
npm run build
cd ..
```

### Step 7: Configure Database or Offline Mode
- **Option A (Connected Mode with Docker PostGIS):**
  ```powershell
  docker-compose up -d
  # Restore canonical database dump
  Get-Content data/backups/vayumarg_f0_backup.sql | docker exec -i vayumarg-postgis psql -U vayumarg_user -d vayumarg
  ```
- **Option B (Zero-Dependency Offline Mode):**
  No Docker or database required; Vayumarg automatically serves all landmark cyclones from `data/demo_cache/`.

### Step 8: Execute Automated Scientific Verification
```powershell
.venv\Scripts\python.exe -m pytest tests/unit/ -v
```
Assert that all core tests pass.

### Step 9: Launch Vayumarg Studio
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_hackathon_demo.ps1
```
Open `http://127.0.0.1:8000/` in browser to verify full functionality.

---

## 3. Isolated Restoration Simulation Test

An automated restoration test was executed in an isolated temporary directory (`tempfile.TemporaryDirectory`):
- **Test Asset:** `reports/v3/VAYUMARG_DRIVE_CONNECTION_TEST.md`
- **Original Pre-computed SHA-256:** `7f9aa211e6cf1c6eafd5585985c6aabb5e5965afb7c50d543340f459eb041df7`
- **Restored Destination SHA-256:** `7f9aa211e6cf1c6eafd5585985c6aabb5e5965afb7c50d543340f459eb041df7`
- **Result:** **100% BITWISE EQUALITY VERIFIED**. Zero local project files were overwritten.

