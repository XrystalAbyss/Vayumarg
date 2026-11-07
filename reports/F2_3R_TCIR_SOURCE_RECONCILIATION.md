# Vayumarg — Milestone F2.3R Official TCIR Publisher Source Reconciliation Report

**Date:** 01 November 2026  
**Status:** **AUDITED, NAMING RECONCILED & RESEARCH GATED**  
**Role:** Principal Scientific Data Auditor & Satellite Remote-Sensing Specialist  
**Milestone:** F2.3R (Authentic Satellite Acquisition Reconciliation)

---

## 1. Executive Summary

Milestone F2.3 referred to an archive named `TCIR-IO.h5` (~14.2 GB). 
This audit inspected the official primary publisher page hosted by Professor Hsuan-Tien Lin at National Taiwan University (NTU CSIE) to reconcile official naming conventions, archive structures, licensing, and remote retrieval feasibility.

---

## 2. Official Publisher & File Naming Reconciliation

- **Official Publisher URL:** `https://www.csie.ntu.edu.tw/~htlin/program/TCIR/`
- **Primary Peer-Reviewed Reference:**
  > Boyo Chen, Buo-Fu Chen, and Hsuan-Tien Lin. *Rotation-blended CNNs on a New Open Dataset for Tropical Cyclone Image-to-intensity Regression.* Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD), pp. 90–99, August 2018.

### 2.1 The `TCIR-IO.h5` Naming Discrepancy Resolved
On the official NTU CSIE publisher portal, the global dataset is partitioned into **two monolithic regional tarballs**:
1. `TCIR-ATLN_EPAC_WPAC.tar.gz` (Atlantic, Eastern Pacific, Western North Pacific)
2. `TCIR-CPAC_IO_SH.tar.gz` (Central Pacific, Indian Ocean, Southern Hemisphere)

**Scientific Finding:**
- There is **no distinct official publisher file named `TCIR-IO.h5` alone**.
- The name `TCIR-IO.h5` used in earlier project notes refers to an unofficial extracted mirror or a community repackaging (e.g. Kaggle `tcir-dataset`).
- In the authentic publisher distribution, Indian Ocean cyclones are bundled together with Central Pacific and Southern Hemisphere cyclones in `TCIR-CPAC_IO_SH.tar.gz`.

---

## 3. Remote Retrieval Feasibility & Technical Barriers

1. **Monolithic Tarball Distribution:**
   - Because the data are published as compressed `.tar.gz` files containing chunked HDF5 matrices, **HTTP byte-range partial slicing is completely unsupported**.
   - Acquiring the Indian Ocean cyclones requires downloading the entire multi-gigabyte regional tarball.
2. **Hemispheric Coriolis Inversion:**
   - The archive pools South Indian Ocean (`SI`) and North Indian Ocean (`NI`) systems.
   - Tropical cyclones in the Southern Hemisphere rotate **clockwise**; North Indian Ocean cyclones rotate **counter-clockwise**.
   - Pooling SH and NH cyclones without spatial flipping disrupts convolutional filters trained on spiral rainband orientation.
3. **Wind Averaging Incompatibility:**
   - TCIR labels are sourced exclusively from JTWC advisories (**1-minute sustained wind speed**).
   - Vayumarg's regional standard (RSMC New Delhi / IMD) is the **3-minute sustained wind speed**.
   - Direct unconditioned loss regression across both datasets introduces a 10%–15% systematic intensity bias.

---

## 4. Formal Research Recommendation for Milestone F2.4

1. **Maintain Zero-Download Policy for F2.3R:**
   - In accordance with milestone restrictions, **no large TCIR archive was downloaded**.
2. **Designated Scientific Role:**
   - Authentic TCIR data should **never replace native ISRO INSAT-3DR/3DS observations** as the operational regional test benchmark.
   - If acquired in future milestones, TCIR should be utilized strictly for **auxiliary cross-basin representation pre-training** (e.g., self-supervised contrastive learning or foundation model pre-training), with explicit filtering for `basin == 'NI'` and secondary mapping to JTWC labels.
3. **Licensing & Attribution:**
   - TCIR is released under Creative Commons Attribution 4.0 International (CC BY 4.0). Any model incorporating TCIR pre-training weights must formally cite Chen et al. (KDD 2018; IEEE TGRS 2020).

