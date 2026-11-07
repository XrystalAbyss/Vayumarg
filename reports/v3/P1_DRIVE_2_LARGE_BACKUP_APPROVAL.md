# VAYUMARG 3.0 — P1-DRIVE.2 LARGE BACKUP APPROVAL & INCREMENTAL ENGINE SPECIFICATION

**Document Version:** 1.0.0  
**Audit Date:** 7 November 2026, 16:30 IST  
**Architect:** Backup & Disaster Recovery Architect & Information Security Lead  
**Target Root:** `18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth` (`Vayumarg`)  
**Approval Status:** **PENDING EXPLICIT USER DECISION FOR TIER 2**  

---

## 1. Audit of Current Backup Script Capabilities

An architectural audit of `scripts/backup/init_drive_workspace.py` was conducted to distinguish **implemented** capabilities from **proposed / designed** capabilities:

| Capability | Current Script State | Status | Implementation Mechanism |
| :--- | :--- | :--- | :--- |
| **Root Folder Verification** | Fully Implemented | **VERIFIED** | `gdrive readonly info` with identity & ownership assertions |
| **Idempotent Hierarchy Creation** | Fully Implemented | **VERIFIED** | Directory scan before `mkdir`; zero duplicate folders created |
| **Direct File Upload** | Fully Implemented | **VERIFIED** | `gdrive mutate upload` with target parent IDs |
| **Isolated Readback Check** | Fully Implemented | **VERIFIED** | Download to temp directory + SHA-256 bitwise comparison |
| **Transfer Ledger Generation** | Fully Implemented | **VERIFIED** | Writes machine-readable JSON ledger with remote IDs and hashes |
| **Delta / Manifest Comparison** | Not Implemented | **PLANNED** | Currently hardcoded for Tier 1 bootstrap; lacks dynamic manifest diffing |
| **Resumable Chunked Uploads** | Not Implemented | **PLANNED** | Large files (>100 MB) rely on CLI single-stream upload |
| **Drive Quota Pre-Check** | Not Implemented | **PLANNED** | No pre-upload Drive storage quota query |
| **Automatic Retries / Backoff** | Not Implemented | **PLANNED** | Fails fast on network timeout |
| **Immutable Snapshots** | Not Implemented | **PLANNED** | Direct file placement; no timestamped versioning directory |
| **Background Scheduling** | Not Implemented | **PLANNED** | Manually executed; zero crons or daemons installed |

---

## 2. Proposed Specification for Vayumarg Incremental Backup Engine (v3.1)

Before automating ongoing transfers, the backup script will be refactored into `scripts/backup/incremental_backup_engine.py` following these design rules:

1. **Manifest Delta Engine:**
   - Scan local filesystem and load `reports/v3/scientific_asset_inventory.json`.
   - Query remote Google Drive folder registry and read remote ledger `reports/v3/transfer_ledger.json`.
   - Compute delta:
     $$\Delta = \{f \in \text{Local} \mid \text{hash}(f) \ne \text{remote\_hash}(f) \land f \notin \text{Excluded}\}$$
2. **Immutable Snapshot Structure:**
   Snapshots will be written to `06_Backups/` with ISO timestamps (e.g., `2026-11-07T160000Z_snapshot/`) so previous backups are never mutated or overwritten.
3. **Chunked & Resumable Large-File Uploads:**
   For assets > 100 MB (`satellite_cnn_best.pt` at 129 MB, raw HDF5 at ~300 MB), use resumable upload protocols with retry exponential backoff.
4. **Safety & Policy Guardrails:**
   - **No Auto-Deletion:** Remote files are never deleted by local synchronizer.
   - **No Implicit Overwrites:** If a remote file ID exists with differing hash, version it with a timestamp suffix.
   - **Pre-Flight Quota Check:** Abort if remaining Google Drive storage is less than $1.2 \times \text{proposed payload}$.
   - **Strict Human Approval Gate:** Large transfers (>100 MB) require explicit CLI confirmation flag (`--approve-large-transfer`).

---

## 3. Tier 2 Transfer Candidates & Exact Authorization Request

The following scientific assets have completed pre-flight security and integrity checks and are staged for upload upon user authorization:

| Category | Local Path | Target Google Drive Subfolder & ID | Files | Binary Size (MiB) | Decimal Size (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ML Models** | `models/vayumarg/vision/satellite_cnn_best.pt` | `03_Trained_Models/Satellite_CNN`<br>`1FlUO_w-G-SkwWOZvmq0zS9ELWSqqsftd` | 1 | 129.16 MiB | 135.43 MB |
| **ML Models** | `models/vayumarg/vision/satellite_convlstm_best.pt` | `03_Trained_Models/Satellite_ConvLSTM`<br>`1cEZ3nyXF9V2oHsVDEnQuyaxiHyROUUCt` | 1 | 4.15 MiB | 4.35 MB |
| **ML Models** | `models/vayumarg/track_gru_best.pt` | `03_Trained_Models/Track_GRU`<br>`1KHmwAFjwzdofU_F9vtBdvBudxSHplugz` | 1 | 1.65 MiB | 1.73 MB |
| **ML Models** | `models/vayumarg/track_hybrid_residual_best.pt` | `03_Trained_Models/Hybrid_Residual`<br>`16Em3C-adxH--TqZndCvqPzBWdi0ocPfE` | 1 | 0.20 MiB | 0.21 MB |
| **Database** | `data/backups/vayumarg_pre_f1_1_backup.sql` | `06_Backups/Scientific_Data_Archives`<br>`13exJOQnI64GNZs3OiTXz-GvX0x4-FSFw` | 1 | 40.12 MiB | 42.07 MB |
| **Processed**| `data/processed/satellite/crops/*.h5` | `02_Scientific_Datasets/ISRO_INSAT`<br>`1v671NHgvlfaAaDCuiTTIYYgswGu_93JD` | 5 | 2.59 MiB | 2.72 MB |
| **TIER 2 TOTAL**| **Staged Transfer Package** | **Designated Drive Hierarchy** | **10** | **177.87 MiB** | **186.51 MB** |

---

## 4. Final Verification State Matrix

| Audit Dimension | Target Requirement | Evaluation Status | Summary Evidence |
| :--- | :--- | :--- | :--- |
| **Phase A: Inventory Reconciliation** | 3,215 files (2,330.80 MiB) | **VERIFIED** | 343 omitted files (25.43 MiB) accounted for across 5 categories |
| **Phase B: Existing Receipt Audit** | 5 Drive files bitwise verified | **VERIFIED** | All 5 files confirmed `VERIFIED_BYTE_FOR_BYTE` via live download |
| **Phase C: Checkpoint Preservation** | 4 model checkpoints audited | **VERIFIED (STAGED)** | 135.16 MiB staged; `weights_only` safe; no secrets |
| **Phase D: Database Dump Security** | PostGIS SQL dump audited | **VERIFIED (STAGED)** | Clean pg_dump; 0 auth statements; matches ORM schema |
| **Phase E: Git Recovery Status** | GitHub backup readiness | **BLOCKED** | Local git has 0 commits and no remote; GitHub tree is empty |
| **Phase F: Restoration Smoke Test** | Download & checksum test | **VERIFIED** | Restored in 1.907s with zero local file modification |
| **Phase G: Incremental Engine** | Dynamic backup daemon | **PARTIAL** | Folder init & bootstrap done; incremental sync planned |
| **Tier 2 Execution Gate** | Upload 177.87 MiB models/DB | **AWAITING APPROVAL** | Held locally pending explicit owner authorization |

---

## 5. Explicit Decision Request for the User

To proceed with **Tier 2 Cloud Preservation (177.87 MiB / 186.51 MB across 10 files)**:
1. Confirm authorization to transfer the four trained PyTorch model checkpoints to Google Drive folder `03_Trained_Models/`.
2. Confirm authorization to transfer the sanitized PostGIS database backup to Google Drive folder `06_Backups/Scientific_Data_Archives/`.
3. Confirm authorization to transfer the five calibrated multi-channel INSAT HDF5 crops to `02_Scientific_Datasets/ISRO_INSAT/`.

