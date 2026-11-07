# Vayumarg — Milestone F2.3R F2.4 Dataset Expansion Readiness Assessment

**Date:** 01 November 2026  
**Status:** **STRATEGICALLY ASSESSED & ROADMAP FORMALIZED**  
**Role:** Principal Scientific Data Architect, ML Infrastructure Engineer, Independent QA Lead  
**Milestone:** F2.3R (Authentic Satellite Acquisition Reconciliation)

---

## 1. Executive Notice & Storage Baseline

- **Current Free Storage on Drive C:** **59.48 GB** (Total capacity: 475.67 GB).
- **MK11 Storage Notice:** The project owner confirmed that unrelated game installation activity (Mortal Kombat 11) accounted for previous drive usage changes. In strict adherence to Section 5, **no game files or unrelated applications were investigated or modified**.
- **Vayumarg Current Storage Footprint:**
  - Completed authentic raw granule: 1 file (**280.64 MB**).
  - Incomplete `.part` files: 2 files (**165.00 MB**).
  - Processed HDF5 crops: 2 files (**0.70 MB**).
  - Total Vayumarg satellite data usage: **446.34 MB** (< 1% of drive).
- **Adequacy:** 59.48 GB provides ample safe headroom for controlled multi-storm acquisition (< 15 GB).

---

## 2. Empirical Lessons from F2.3 Acquisition Bottlenecks

Forensic analysis of the F2.3 batch run yielded critical empirical throughput metrics:
1. **Server Throttling:** MOSDAC download endpoints throttle single-stream downloads to $\sim 150 - 350\text{ KB/s}$. A single ~280 MB file requires 12 to 20 minutes of continuous transfer.
2. **Socket Dropouts & Lack of Resume:**
   - In `mdapi.py`, downloads stream into `<filename>.part`.
   - When network streams drop mid-transfer (e.g. after 30 MB or 135 MB), the lack of HTTP `Range: bytes=<offset>-` headers causes subsequent attempts to restart from byte 0, repeatedly exhausting transfer timeouts.
3. **Storage Efficiency of Crops:**
   - A full-disk L1B file is $\sim 280\text{ MB}$.
   - An extracted $800\text{ km} \times 800\text{ km}$ ($201 \times 201$) multichannel crop is **$\approx 618\text{ KB}$** ($0.22\%$ of raw size).
   - Once crops are extracted and verified by SHA-256 in PostgreSQL, retaining only crops allows storing **1,000 cyclone observations in ~620 MB**!

---

## 3. Strategic Acquisition Options for Milestone F2.4

| Strategic Option | Scope & Target | Raw Storage | Processed Crops | Network Duration | Scientific Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Option A: Conservative Recovery Cohort (Recommended)** | **6 storms, 18 granules** (3 per storm: weak, peak, landfall) | **$\sim 5.2\text{ GB}$** | **$\sim 11\text{ MB}$** | $\sim 3\text{ hours}$ (phased batches) | Immediate verification of F2.3 targets with HTTP resume; low risk |
| **Option B: Balanced Decadal Benchmark** | **20 storms, 80 granules** (2018–2024, 15 BoB / 5 ARB) | **$\sim 23.5\text{ GB}$** | **$\sim 50\text{ MB}$** | $\sim 12\text{ hours}$ (scheduled off-peak) | High statistical power for SIH 2026 Module A CNN baseline training |
| **Option C: Comprehensive Foundation** | **50 storms, 300 granules** (2014–2024 decadal archive) | **$\sim 88.0\text{ GB}$** | **$\sim 185\text{ MB}$** | Dedicated background daemon | Requires external drive or automated raw purge pipeline |

---

## 4. Immediate Engineering Prerequisites for F2.4

Before authorizing any download in Milestone F2.4:
1. **Implement HTTP Range Resume:** Upgrade `SecureMOSDACDownloader` to inspect existing `.part` files and pass `headers={'Range': f'bytes={existing_size}-'}` to resume interrupted streams.
2. **Per-Granule Verification Gating:** Process and register each granule immediately upon download completion rather than running unbounded multi-file batch loops.
3. **Synoptic Subsampling:** Filter candidate acquisitions to synoptic intervals ($\Delta t \ge 3\text{ hours}$), eliminating redundant 4-minute rapid-scan frames.

