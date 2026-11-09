# VAYUMARG 3.0 — P1.1R-S SATELLITE SCREENSHOT DISCLOSURE & DATA GOVERNANCE AUDIT

**Document ID:** `reports/v3/P1_1R_S_SCREENSHOT_DISCLOSURE.md`  
**Milestone:** P1.1R-S Release Gate  
**Data Governance Lead:** Principal Scientific Software Verification Engineer & Application Security Engineer  
**Date:** 2026-11-09  
**Repository Scope:** `reports/v3/screenshots/` (12 Image Files, ~1.7 MB)  

---

## 1. Context & Objective

In milestone `P1.1R-FINAL`, 12 browser acceptance screenshots were captured and committed to `reports/v3/screenshots/` to verify full-stack React/FastAPI integration.

This audit evaluates:
1. Compliance with ISRO MOSDAC Level 1B data dissemination policies regarding public GitHub distribution.
2. Privacy, local host environment leakage (paths, tokens, user data).
3. The technical remediation required to maintain security boundaries while preserving local verification evidence.

---

## 2. Screenshot File Inventory & Radiometric Content Analysis

| File Name | Physical Size | Screen View / Subject | Data Provenance | Public Policy Assessment |
| :--- | :--- | :--- | :--- | :--- |
| `01_overview_acceptance.png` | 125,994 B | Synoptic Overview & Storm Catalog | IBTrACS Track Metadata | Public Domain (NOAA) |
| `02_satellite_ops_acceptance.png` | 165,340 B | Multichannel Remote Sensing View | **ISRO MOSDAC Level 1B TIR-1 (10.8 µm)** | **PROPRIETARY DERIVED IMAGERY** |
| `03_satellite_wv_channel_acceptance.png` | 142,252 B | Water Vapor Channel (6.9 µm) | **ISRO MOSDAC Level 1B WV (6.9 µm)** | **PROPRIETARY DERIVED IMAGERY** |
| `04_dana_satellite_governance_acceptance.png` | 129,667 B | Cyclone DANA Landfall Evaluation | **ISRO MOSDAC Level 1B TIR-1** | **PROPRIETARY DERIVED IMAGERY** |
| `05_forecast_generation_acceptance.png` | 109,165 B | Geodesic Projection Map (+24h) | IBTrACS Historical Track | Public Domain (NOAA) |
| `06_hindsight_verification_acceptance.png` | 115,004 B | Track Error Hindsight Analysis | Mathematical Geodesic Error | Public Domain (NOAA) |
| `07_ai_model_lab_cnn_acceptance.png` | 170,722 B | AI Lab CNN Intensity Architecture | **TIR-1 Intensity Tensor Visualization** | **PROPRIETARY DERIVED IMAGERY** |
| `08_ai_model_lab_convlstm_acceptance.png` | 97,951 B | AI Lab ConvLSTM Spatiotemporal | Model Topology Graph | Scientific Code / Architecture |
| `09_ai_model_lab_track_gru_acceptance.png` | 118,742 B | AI Lab GRU Geodesic Displacement | Loss Curves & Metrics | Scientific Code / Architecture |
| `10_model_audit_release_ledger_acceptance.png`| 110,874 B | Cryptographic Checksum Ledger | Model Checksum Metadata | Public Verification Ledger |
| `11_methodology_disclaimers_acceptance.png` | 119,184 B | Methodology & Research Limitations | Disclaimers & Formulas | Open Research Documentation |
| `12_satellite_dataset_gallery_acceptance.png` | 419,894 B | 4-Storm Multichannel Grid (16 bands) | **ISRO MOSDAC Level 1B Multi-channel** | **PROPRIETARY DERIVED IMAGERY** |

---

## 3. Legal & Regulatory Compliance Findings

### 3.1 ISRO MOSDAC Level 1B Telemetry Policy
ISRO MOSDAC Level 1B data is provided under meteorological research agreements. While academic algorithms, scientific validation summaries, and code are open under the project's MIT license, **redissemination of authentic satellite imagery products or high-resolution rendered raster scenes to public open-source code hosts without formal distribution agreements is restricted**.

### 3.2 Privacy & Infrastructure Leakage Check
- **Filesystem Paths:** No local Windows usernames (`C:\Users\...`) or absolute machine paths are visible in the captured browser viewports.
- **Network Endpoints:** Only local loopback (`http://127.0.0.1:8000` / `http://localhost:5173`) was rendered.
- **Authentication Tokens:** No active tokens, passwords, or cookies were displayed in the UI elements.

### Conclusion:
The 5 screenshots rendering authentic ISRO satellite imagery (`02`, `03`, `04`, `07`, `12`) should **not** be tracked in the public Git repository.

---

## 4. Remediation Executed

1. **Untracked from Git Index:**
   ```bash
   git rm -r --cached reports/v3/screenshots/
   ```
2. **Ignored in `.gitignore`:**
   Added the following entries to `.gitignore`:
   ```gitignore
   # Visual verification screenshots & proprietary satellite imagery
   reports/v3/screenshots/
   tests/artifacts/
   ```
3. **Local Preservation:**
   All 12 original PNG files remain physically untouched on the local workstation disk at `reports/v3/screenshots/` for internal QA, reproducibility review, and offline audits.
