# Vayumarg — Milestone F2.2 Module A Data Contract & Readiness Report

**Date:** 01 November 2026  
**Status:** CONTRACT FROZEN & ML READY  
**Author:** Python ML Infrastructure Engineer & Scientific Data Architect  
**Milestone:** F2.2 (Scientific Dataset Readiness)

---

## 1. Executive Summary

Milestone F2.2 formalizes the canonical data contract between Vayumarg's shared scientific repository and **Module A** (Satellite-Based Cyclone Classification and Intensity Estimation). 
This contract solves the sample duplication risk identified in earlier pilot phases, strictly enforces multi-agency wind segregation, and establishes immutable eligibility gating for ML pipelines.

---

## 2. Sample Deduplication Architecture

### 2.1 The Pilot Contamination Vulnerability
In the preliminary F2 design, relational queries joining `satellite_processed_crops` to `satellite_track_associations` produced duplicate rows whenever an image matched both IMD and JTWC track observations. An uncurated ML dataset would feed two identical image tensors with slightly different wind speed labels (e.g., 60 kts vs 55 kts) into training batches, leading to data leakage, contradictory loss gradients, and inflated validation scores.

### 2.2 The Canonical Solution
In `src/vayumarg/contracts/export.py`, the exporter function `export_module_a_multichannel_dataset()` establishes:
- **Atomic Unit:** Exactly **one sample record per processed image crop**.
- **Multi-Agency Label Segregation:** Primary agency (IMD) and secondary agency (JTWC) labels are encapsulated within the same sample record.
- **Deduplication Invariant:**
  $$\text{Count}(\text{Exported Samples}) \equiv \text{Count}(\text{Unique Eligible Image Crops})$$

```json
{
  "sample_id": "38d72111-c918-450f-a496-e137836ea1f8",
  "storm_sid": "2024146N2189",
  "storm_canonical_name": "REMAL",
  "image_path": "data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5",
  "image_sha256": "7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90",
  "tensor_shape": [2, 201, 201],
  "channels": ["TIR1", "WV"],
  "effective_resolutions_km": [4.0, 8.0],
  "labels": {
    "primary_imd": {
      "agency": "IMD",
      "wind_kt": 60.0,
      "wind_averaging_minutes": 3,
      "pressure_hpa": 978.0,
      "cyclone_category": "SCS",
      "spatial_offset_km": 1.03,
      "temporal_offset_seconds": 178
    },
    "secondary_jtwc": {
      "agency": "JTWC",
      "wind_kt": 55.0,
      "wind_averaging_minutes": 1,
      "pressure_hpa": 981.0,
      "cyclone_category": "TS",
      "spatial_offset_km": 91.9,
      "temporal_offset_seconds": 178
    }
  },
  "provenance_status": "REAL_VERIFIED",
  "scientific_quality_status": "AUDITED_VALID",
  "model_eligibility": "TRAIN_TEST_ELIGIBLE"
}
```

---

## 3. Scientific Governance & Status Enums

To ensure zero synthetic data leaks into scientific benchmarks, the system establishes three explicit enum fields (`src/vayumarg/contracts/enums.py`):

1. **`ProvenanceStatus`:**
   - `REAL_VERIFIED`: Authentic, downloaded MOSDAC/ISRO data with verified checksum.
   - `SYNTHETIC_PILOT`: Synthetic test fixture for unit tests or architecture prototypes.
   - `UNVERIFIED_SOURCE`: Data from untrusted or unverified secondary sources.
2. **`ScientificQualityStatus`:**
   - `AUDITED_VALID`: Radiometrically calibrated, georeferenced, non-corrupt.
   - `CALIBRATION_CLAMPED`: Contains valid data but contains pixels hitting calibration saturation floors.
   - `FILL_CONTAMINATED`: More than 20% fill or missing pixels.
   - `REJECTED`: Fails checksum, invalid headers, or geometric corruption.
3. **`ModelEligibility`:**
   - `TRAIN_TEST_ELIGIBLE`: Approved for official model training and benchmarking.
   - `EVALUATION_ONLY`: Valid for qualitative case studies, ineligible for loss training.
   - `SYNTHETIC_TESTING_ONLY`: For code test suites only; strictly excluded from ML datasets.
   - `DISQUALIFIED`: Bad quality or rejected.

---

## 4. Tensor Specification for Module A Model Developers

- **Input Tensor:** Float32 tensor of shape `[N, 2, 201, 201]`.
  - Channel 0: TIR-1 Brightness Temperature ($K$) at native 4.0 km resolution.
  - Channel 1: WV Brightness Temperature ($K$) co-registered from native 8.0 km resolution.
- **Physical Bounding Box:** Fixed $800\text{ km} \times 800\text{ km}$.
- **Target Variables:**
  - Continuous regression target: `labels.primary_imd.wind_kt` (3-minute sustained wind speed in knots).
  - Discrete classification target: IMD Category (e.g., `D`, `DD`, `CS`, `SCS`, `VSCS`, `ESCS`, `SuCS`).
  - Secondary evaluation metric: JTWC 1-minute sustained wind prediction error.

