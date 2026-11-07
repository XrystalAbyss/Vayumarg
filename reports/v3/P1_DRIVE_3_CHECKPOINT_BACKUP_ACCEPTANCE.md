# VAYUMARG 3.0 — P1-DRIVE.3 FOUR-MODEL CHECKPOINT BACKUP & RESTORE ACCEPTANCE REPORT

**Acceptance Date:** 7 November 2026, 16:50 IST  
**Engineers & Auditors:** Senior Scientific Data Engineer, Backup & Disaster Recovery Architect, Machine Learning Engineer & Independent Verification Lead  
**Canonical Google Drive Root:** [`18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth`](https://drive.google.com/drive/folders/18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth) (`Vayumarg`)  
**Target Category:** `03_Trained_Models/`  
**Final Acceptance Verdict:** **VERIFIED_COMPLETE (100% BITWISE READBACK EQUALITY ACROSS ALL 4 CHECKPOINTS)**  

---

## 1. Executive Summary

Under explicit owner authorization, the four genuine, independently evaluated Vayumarg deep-learning model checkpoints were uploaded to their designated private Google Drive subfolders. Each uploaded artifact was downloaded into an isolated local scratch environment, where its complete byte stream was verified against its authoritative SHA-256 cryptographic identity. Zero local checkpoints were modified, zero unauthorized assets were transferred, and local application inference compatibility was empirically demonstrated across all four architectures.

---

## 2. Cloud Checkpoint Verification Ledger

| Model ID & Checkpoint Filename | Drive File ID | Destination Subfolder & ID | Exact Size (Bytes) | Authoritative & Readback SHA-256 Checksum | Upload Timing | Readback Download Timing | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`satellite_cnn_best`**<br>`satellite_cnn_best.pt` | `1uM3hTiQX17JWLJClXJw_hhTm7J3PQnZD` | `03_Trained_Models/Satellite_CNN`<br>`1FlUO_w-G-SkwWOZvmq0zS9ELWSqqsftd` | 135,432,053 B<br>(129.16 MiB) | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` | 139.21s | 248.54s | **VERIFIED_BYTE_FOR_BYTE** |
| **`satellite_convlstm_best`**<br>`satellite_convlstm_best.pt` | `1QGklBkL4_FoIAmFMIeSWdLqYBQPQqpjK` | `03_Trained_Models/Satellite_ConvLSTM`<br>`1cEZ3nyXF9V2oHsVDEnQuyaxiHyROUUCt` | 4,353,804 B<br>(4.15 MiB) | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` | 8.42s | 10.06s | **VERIFIED_BYTE_FOR_BYTE** |
| **`track_gru_best`**<br>`track_gru_best.pt` | `1mFPoUhhSMJ0ZT6L8p7wYUIQjuJm28B0z` | `03_Trained_Models/Track_GRU`<br>`1KHmwAFjwzdofU_F9vtBdvBudxSHplugz` | 1,729,622 B<br>(1.65 MiB) | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` | 28.21s | 7.86s | **VERIFIED_BYTE_FOR_BYTE** |
| **`track_hybrid_residual_best`**<br>`track_hybrid_residual_best.pt` | `1sPtRSI8usMFE31SRwZaE8Bt8AGcuMhuV` | `03_Trained_Models/Hybrid_Residual`<br>`16Em3C-adxH--TqZndCvqPzBWdi0ocPfE` | 210,882 B<br>(0.20 MiB) | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` | 3.77s | 2.52s | **VERIFIED_BYTE_FOR_BYTE** |
| **Cloud Manifest Copy**<br>`checkpoint_cloud_registry.json` | `1D3KNbrSvDBCDStyFi5Re89FXGVTxkweT` | `03_Trained_Models/Model_Manifests`<br>`1PwL6jQ-GKh1CKSXH0VtbUz1bSahaUAu0` | 4,142 B<br>(4.04 KiB) | `8f51a4a408987b7a147aef9348b11c97a8138981df262a4d0ec39174620025fa` | 1.82s | 1.15s | **VERIFIED_BYTE_FOR_BYTE** |
| **TOTALS** | **5 Remote Artifacts** | **Strict Subfolder Hierarchy** | **141,730,503 B**<br>**(135.16 MiB)** | **100% Cryptographic Match** | **181.43s** | **270.13s** | **VERIFIED_COMPLETE** |

---

## 3. Preflight & Environmental Governance

1. **Authenticated Google Drive Identity:**
   - Account: `goyalishaan@gmail.com`
   - Scopes: `https://www.googleapis.com/auth/drive`, `https://www.googleapis.com/auth/userinfo.email`
   - Target Root: `Vayumarg` (`18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth`)
   - Sharing Status: `Shared: false` (**Strictly Restricted to owner**)
2. **Drive Storage Quota Check:**
   - Account Quota: 5,120.0 GB (5.0 TB limit)
   - Used Storage: 29.3 GB (~0.57% utilized)
   - Transferred Payload: 135.16 MiB (0.0026% of quota; zero quota pressure)
3. **Collision & Conflict Avoidance:**
   - All four destination subfolders were verified empty prior to initial upload.
   - For re-runs, the engine checks filename and byte size matching to prevent duplicate object creation.
4. **Zero Local Mutation:**
   - File modification times (`st_mtime`) and cryptographic checksums on the local disk were validated before and after execution; zero local source bytes were altered.

---

## 4. Scientific Provenance & Training Lineage Corrections

In strict accordance with Phase 2 requirements, all scientific references have been corrected to reflect empirical project evidence rather than inherited boilerplate:

### 4.1. Vision Models (CNN & ConvLSTM)
- **Dataset Attribution:** Curated subset of the **NASA Tropical Cyclone Wind Estimation Competition** (DrivenData / NASA IMPACT), **distinct from TCIR** (Tropical Cyclone Image Dataset).
- **Sensor & Band:** Longwave Clean Infrared Window Band 13 (centered at **10.3 µm** on GOES-16/17 ABI and **10.4 µm** on Himawari-8 AHI).
- **Physical Volume:** 2,500 8-bit single-channel normalized grayscale arrays across 25 storm IDs.
- **Partitioning:** Strictly storm-disjoint splits: 15 storms (1,619 images) train, 5 storms (467 images) validation, 5 storms (414 images) held-out test.
- **Label Unit:** 1-minute sustained wind speed in knots (NOAA / JTWC convention).

### 4.2. Trajectory Models (Track GRU & Hybrid Residual)
- **Dataset Attribution:** **NOAA IBTrACS v04r01** historical North Indian Ocean (NIO) cyclone archive spanning 1982 to 2024.
- **Temporal Resolution:** 6-hourly storm fixes with interpolated kinematic derivatives.
- **Input Feature Set:** 10 continuous kinematic features (latitude, longitude, $\Delta\text{lat}$, $\Delta\text{lon}$, translational velocity, heading, central pressure, pressure deficit, and time deltas).
- **Output Forecasts:** Multi-horizon displacement vectors and future intensity at **+6h, +12h, and +24h** forecast horizons.

---

## 5. Application Compatibility & Inference Verification (Phase 6)

Following cloud verification, the local application models and model registry were tested to verify that the local codebase remains 100% operational:

```
[Step 1] Authoritative Model Registry Query:
  Overall Status: OPERATIONAL
  - satellite_cnn:  ResNet18-IR-SingleChannel | Checksum: True | Status: VERIFIED_EXPERIMENTAL
  - convlstm:       CycloneConvLSTM-32-64    | Checksum: True | Status: VERIFIED_EXPERIMENTAL
  - track_gru:      VayumargTrackGRU         | Checksum: True | Status: VERIFIED_EXPERIMENTAL

[Step 2] Satellite CNN Forward Pass:
  [PASS] Loaded 135 state dict keys
  [PASS] Input: (1, 1, 128, 128) -> Wind Speed: 28.35 kts, Category Logits: torch.Size([1, 6])

[Step 3] Satellite ConvLSTM Forward Pass:
  [PASS] Loaded 24 state dict keys
  [PASS] Input: (1, 3, 1, 64, 64) -> Intensity: 31.06 kts, Future Frame: torch.Size([1, 1, 64, 64])

[Step 4] Track GRU Forward Pass:
  [PASS] Loaded 24 state dict keys
  [PASS] Input: (1, 8, 10) -> Displacements: (1, 3, 2), Future Winds: (1, 3)

[Step 5] Track Hybrid Residual Forward Pass:
  [PASS] Loaded 29 state dict keys
  [PASS] Input: (1, 8, 10) -> Displacements: (1, 3, 2), Residuals: (1, 3, 2), Winds: (1, 3)
```

---

## 6. Remaining Risks & Operational Next Steps

1. **GitHub Disaster Recovery Gap:** The local Git repository has zero commits and no configured remote. Source code recovery remains dependent on local disk until a sanitized baseline commit is staged and pushed.
2. **Bulk Raw Data Retention:** 1.76 GB of raw satellite imagery (6 complete MOSDAC HDF5 granules and 2,500 NASA images) and the 40.1 MB PostGIS SQL dump remain local-only.
3. **PyTorch Safe-Loading Deprecation:** `track_hybrid_residual_best.pt` serializes NumPy scalar and dtype attributes in its metadata dictionary, requiring `weights_only=False` or explicit NumPy symbol allowlisting under PyTorch 2.6+.

---

## 7. Final Verification Acceptance Verdict

```
>>> P1-DRIVE.3 VERDICT: VERIFIED_COMPLETE <<<
- 4 of 4 Authorized Model Checkpoints Uploaded & Cataloged
- 100% Bitwise Download Verification Confirmed
- Zero Data Corruption Detected
- Model Registry State: OPERATIONAL
```

