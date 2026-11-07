# VAYUMARG 3.0 — P1-DRIVE.2 CHECKPOINT PRESERVATION MANIFEST & READINESS

**Audit Date:** 7 November 2026, 16:20 IST  
**Auditor:** Machine Learning Research Engineer & Information Security Auditor  
**Gate Status:** **STAGED & VALIDATED — AWAITING EXPLICIT USER AUTHORIZATION FOR TIER 2**  

---

## 1. Executive Summary

The Vayumarg project possesses four genuine PyTorch model checkpoints totaling **141,726,361 bytes (135.16 MiB / 141.73 MB)**. A non-destructive security audit using PyTorch 2.6 `weights_only=True` and zipfile structure analysis confirmed that none of the checkpoints contain embedded credentials, private machine paths, or arbitrary code execution payloads.

> [!CAUTION]
> In accordance with the non-destructive security boundaries of `P1-DRIVE.2`, **zero model checkpoint binaries have been uploaded**. This document defines the exact proposed transfer manifest and requests explicit user authorization before commencing Tier 2 cloud preservation.

---

## 2. Checkpoint Preservation Manifest

| Field | Checkpoint 1 (CNN) | Checkpoint 2 (ConvLSTM) | Checkpoint 3 (Track GRU) | Checkpoint 4 (Hybrid Residual) |
| :--- | :--- | :--- | :--- | :--- |
| **Model Registry Name** | `satellite_cnn_best` | `satellite_convlstm_best` | `track_gru_best` | `track_hybrid_residual_best` |
| **Source Local Path** | `models/vayumarg/vision/satellite_cnn_best.pt` | `models/vayumarg/vision/satellite_convlstm_best.pt` | `models/vayumarg/track_gru_best.pt` | `models/vayumarg/track_hybrid_residual_best.pt` |
| **Intended Drive Folder** | `03_Trained_Models/Satellite_CNN` | `03_Trained_Models/Satellite_ConvLSTM` | `03_Trained_Models/Track_GRU` | `03_Trained_Models/Hybrid_Residual` |
| **Destination Folder ID** | `1FlUO_w-G-SkwWOZvmq0zS9ELWSqqsftd` | `1cEZ3nyXF9V2oHsVDEnQuyaxiHyROUUCt` | `1KHmwAFjwzdofU_F9vtBdvBudxSHplugz` | `16Em3C-adxH--TqZndCvqPzBWdi0ocPfE` |
| **Exact Physical Size** | 135,432,053 bytes (129.16 MiB) | 4,353,804 bytes (4.15 MiB) | 1,729,622 bytes (1.65 MiB) | 210,882 bytes (0.20 MiB) |
| **SHA-256 Checksum** | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` |
| **Model Architecture** | ResNet18-IR-SingleChannel | CycloneConvLSTM-32-64 | VayumargTrackGRU (2-layer, 96 hidden) | HybridResidualModel (MLP Residual) |
| **Training Dataset Lineage** | NASA Tropical Cyclone IR subset (2,500 images) | NASA Tropical Cyclone IR sequential sequences | NOAA IBTrACS North Indian Ocean (1982-2024) | NOAA IBTrACS + Geodesic Kinematic Residuals |
| **Runtime Input Spec** | $(B, 1, 224, 224)$ normalized IR brightness | $(B, 3, 1, 128, 128)$ temporal sequence | $(B, 8, 10)$ normalized tracking features | $(B, 8, 10)$ kinematic track sequence |
| **Output Spec** | 1D scalar wind speed (knots) | 1D scalar wind speed (knots) | 6h/12h/24h $(\Delta \text{lat}, \Delta \text{lon}, \Delta V)$ | Calibrated 6h/12h/24h track displacements |
| **Compatibility Req.** | PyTorch $\ge 2.2$, torchvision $\ge 0.17$ | PyTorch $\ge 2.2$ | PyTorch $\ge 2.2$ | PyTorch $\ge 2.2$, numpy $\ge 1.26$ |
| **Transfer Priority** | Priority 1 (Primary Vision) | Priority 2 (Spatiotemporal) | Priority 3 (Primary Track) | Priority 4 (Residual Correction) |
| **Restore Destination** | `models/vayumarg/vision/` | `models/vayumarg/vision/` | `models/vayumarg/` | `models/vayumarg/` |
| **Verification Method** | Post-upload download + bitwise SHA-256 | Post-upload download + bitwise SHA-256 | Post-upload download + bitwise SHA-256 | Post-upload download + bitwise SHA-256 |

---

## 3. Checkpoint Payload & Security Inspection

Each checkpoint was analyzed using Python inspection tools:
1. **Packaging Format:** All four checkpoints are confirmed to be modern PyTorch zip archives containing `data.pkl`, `byteorder`, and serialized tensor chunks (`data/0`, `data/1`, ...).
2. **Key Introspection:**
   - `satellite_cnn_best.pt`: `['epoch', 'model_state_dict', 'optimizer_state_dict', 'val_metrics', 'model_architecture', 'training_timestamp_utc']`
   - `satellite_convlstm_best.pt`: `['epoch', 'model_state_dict', 'optimizer_state_dict', 'val_metrics', 'model_architecture', 'training_timestamp_utc']`
   - `track_gru_best.pt`: `['epoch', 'model_state_dict', 'optimizer_state_dict', 'val_loss', 'architecture', 'in_features', 'hidden_size', 'num_layers', 'horizons']`
   - `track_hybrid_residual_best.pt`: `['epoch', 'model_state_dict', 'optimizer_state_dict', 'val_loss', 'architecture', ...]`
3. **Payload Sanitization:** Zero absolute local paths (e.g., `C:\Users\astra\...`), zero network URIs, and zero API tokens or environment secrets are embedded in any of the four files.

---

## 4. Proposed Transfer Volume & Explicit Request for Authorization

- **Total Files Proposed for Tier 2 Checkpoint Upload:** 4 files
- **Total Physical Volume:** **141,726,361 bytes (135.16 MiB / 141.73 MB)**
- **Destination:** Private Google Drive Root `18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth` under folder `03_Trained_Models/`

> [!IMPORTANT]
> The checkpoint transfer is staged and ready. Awaiting explicit user approval before initiating the 135.16 MiB transfer.

