# Vayumarg — Milestone F2.3R Database Integrity & Source Provenance Reconciliation Report

**Date:** 01 November 2026  
**Status:** **RECONCILED & SCIENTIFICALLY GATED**  
**Role:** Principal Scientific Data Auditor, PostgreSQL/PostGIS Architect  
**Milestone:** F2.3R (Authentic Satellite Acquisition Reconciliation)

---

## 1. Executive Summary

This report establishes the verified state of the primary research database `vayumarg` (PostgreSQL 16.4 / PostGIS 3.4.3 on port 5433).
The database contains **zero corrupt or partial records** from the interrupted F2.3 acquisition attempt, fully preserves the historical NOAA IBTrACS NI baseline, and maintains complete quarantine over the F2 synthetic test fixtures.

---

## 2. Table-by-Table Database Population Audit

Direct SQL counts executed against `vayumarg`:

| Relational Table | Row Count | Scientific Classification | Invariant Check |
| :--- | :--- | :--- | :--- |
| `data_sources` | **1** | NOAA IBTrACS v04r01 Provider | Exact match |
| `source_assets` | **1** | Authentic raw IBTrACS CSV archive | Exact match |
| `ingestion_runs` | **2** | Ingestion run history (F1, F1.1) | Exact match |
| `storms` | **1,860** | Canonical North Indian Ocean Cyclones (1842–2024) | Exact match |
| `track_observations` | **104,374** | Dual-agency IMD & JTWC synoptic fixes | Exact match |
| `data_quality_issues`| **8** | Documented IBTrACS wind/season anomalies | Exact match |
| `dataset_snapshots` | **1** | F1.1 frozen scientific baseline snapshot | Exact match |
| `satellite_products`| **10** | Registered sensor products (INSAT-3D/3DR/3DS, TCIR) | Exact match |
| `satellite_granules`| **2** | **1 `REAL_VERIFIED`**, **1 `SYNTHETIC_FIXTURE`** | Exact match |
| `satellite_processed_crops` | **13** | **1 `REAL_VERIFIED`**, **12 `SYNTHETIC_FIXTURE`** | Exact match |
| `satellite_track_associations` | **23** | **2 `REAL_VERIFIED`**, **21 `SYNTHETIC_FIXTURE`** | Exact match |

---

## 3. Independent Image-Count & Sample Reconciliation

To prevent inflated sample reporting, distinct counts are established across every abstraction tier:

1. **Raw Source Granules:** **1 authentic completed file** (`3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5`, 280.64 MB). Two partial `.part` files exist on disk but are excluded from database registration.
2. **Unique Satellite Acquisitions:** **1** (INSAT-3DR Imager, 2024-05-26 18:02:58 to 18:07:16 UTC).
3. **Unique Source Image Times:** **1** (approximate storm observation time: 18:04:15 UTC).
4. **Native-Channel Images:** **2** (TIR-1 at 4.0 km, WV at 8.0 km).
5. **Calibrated Physical Channels:** **2** (both converted to Brightness Temperature $K$ via onboard LUTs).
6. **Processed Multichannel Crops:** **1** (`data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5`, 633,554 bytes).
7. **Unique Cyclone/Time Examples:** **1** (Cyclone REMAL at peak landfall).
8. **IMD Label Associations:** **1** (3-minute sustained wind: 60 kts, central pressure: 978 hPa, category: Severe Cyclonic Storm).
9. **JTWC Label Associations:** **1** (1-minute sustained wind: 55 kts, central pressure: 981 hPa, category: Tropical Storm).
10. **Independent Model-Eligible Samples:** **1** (strictly deduplicated: one atomic image crop carrying dual-agency target labels).

---

## 4. Planned vs Actual Outcome Reconciliation

| Milestone Stage | Planned in F2.3 | Actually Achieved in F2.3R | Discrepancy Analysis |
| :--- | :--- | :--- | :--- |
| **Granules Targeted** | 6 granules | 6 granules targeted | Exact manifest prepared |
| **Downloads Completed**| 6 granules | **0 granules** | Network disconnects / stream timeouts |
| **Partial Downloads** | 0 | **2 granules** (`.part` files) | 30 MB Remal, 135 MB Dana partials |
| **Failed Downloads** | 0 | **1 granule** | Stream failed with 0 bytes |
| **Unattempted** | 0 | **3 granules** | Stopped before attempting |
| **New Crops Generated**| 6 crops | **0 crops** | Pipeline correctly gated on valid HDF5 |
| **New DB Records Added**| 6 granules / 6 crops | **0 records** | Zero unverified or partial data added |
| **Model-Ready Dataset** | 7 samples | **1 sample** (Baseline preserved) | **`PARTIAL_ACQUISITION`** |

---

## 5. Provenance & Quarantine Verdict

- **Authentic Data Integrity:** The single authentic baseline sample remains completely intact and verified.
- **Quarantine Gating:** All 12 synthetic pilot crops and 21 synthetic associations remain tagged `SYNTHETIC_FIXTURE` and are excluded from all production ML dataset queries.
- **Database Cleanliness:** The PostgreSQL database is completely free of phantom records, broken foreign keys, or partial assets.

