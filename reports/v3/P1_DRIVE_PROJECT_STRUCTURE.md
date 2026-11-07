# VAYUMARG 3.0 — P1 GOOGLE DRIVE PROJECT STRUCTURE SPECIFICATION

**Document Version:** 1.0.0  
**Date:** 7 November 2026  
**Auditor:** Scientific Data Infrastructure Architect  
**Root Folder ID:** `18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth`  
**Root Folder URL:** `https://drive.google.com/drive/folders/18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth`  

---

## 1. Directory Tree Specification

The designated Vayumarg scientific Google Drive folder (`18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth`) is structured into seven primary functional partitions:

```
18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth (VAYUMARG ROOT)
├── 01_Project_Management/
│   ├── Milestones/
│   ├── Governance/
│   └── Resource_Budgets/
├── 02_Scientific_Datasets/
│   ├── NASA_Tropical_Cyclone/
│   │   ├── Curated_Subset_Manifests/
│   │   └── Benchmark_Images_Archive/
│   ├── NOAA_IBTrACS/
│   │   ├── Raw_Archives/
│   │   └── Filtered_NIO_Cohorts/
│   ├── ISRO_INSAT/
│   │   ├── Level1B_Granules/ (PENDING LICENSE REVIEW)
│   │   ├── Calibrated_Multichannel_Crops/
│   │   └── Radiometric_Calibration_LUTs/
│   ├── Environmental_Data/
│   │   └── Reanalysis_Steering_Cutouts/
│   └── Dataset_Manifests/
├── 03_Trained_Models/
│   ├── Satellite_CNN/
│   │   ├── Checkpoints/
│   │   └── Architecture_Specs/
│   ├── Satellite_ConvLSTM/
│   │   ├── Checkpoints/
│   │   └── Sequence_Configs/
│   ├── Track_GRU/
│   │   └── Checkpoints/
│   ├── Hybrid_Residual/
│   │   └── Checkpoints/
│   └── Model_Manifests/
├── 04_Research_Experiments/
│   ├── Module_A/
│   ├── Module_B/
│   ├── Evaluation_Ledgers/
│   ├── Research_Plots/
│   └── Experiment_Manifests/
├── 05_Project_Documentation/
│   ├── Architectural_Specifications/
│   ├── Operational_Manuals/
│   └── Scientific_Reports/
├── 06_Backups/
│   ├── Source_Snapshots/
│   ├── Model_Checkpoint_Snapshots/
│   ├── Scientific_Data_Archives/
│   └── Recovery_Manifests/
└── 07_Team_Collaboration/
    ├── Meeting_Minutes/
    └── Review_Presentations/
```

---

## 2. Idempotency & Creation Invariants

To ensure safe, automated folder creation upon OAuth authorization:
1. **Idempotent Lookups:** Before issuing any `create_folder` API request, the system queries child folders under parent `18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth` by exact name and MIME type (`mimeType = 'application/vnd.google-apps.folder' and trashed = false`). If the folder already exists, its existing folder ID is recorded without creating duplicates.
2. **Strict Parent Bounding:** Every subfolder creation request explicitly binds `parents: ['18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth']` or the verified ID of its respective parent subfolder. No folders shall ever be created in the user's root "My Drive".
3. **Restricted Sharing Preservation:** Google Drive automatically inherits permissions from the parent folder. Because `18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth` is set to **Restricted**, all child folders will automatically inherit Restricted private status. The system will never call permissions APIs to broaden access.
4. **No Third-Party Moving:** The integration operates strictly inside the designated folder boundary; it has zero access to, and will never move or alter, any unrelated folders in the owner's Google Drive.

