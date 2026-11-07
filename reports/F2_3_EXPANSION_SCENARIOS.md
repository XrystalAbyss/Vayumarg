# Vayumarg — Milestone F2.3 Dataset Expansion Scenarios & Strategic Acquisition Roadmap

**Date:** 01 November 2026  
**Status:** **ARCHITECTED & STRATEGICALLY PLANNED**  
**Role:** Principal Scientific Data Architect, ML Infrastructure Engineer, Meteorological Research Scientist  
**Milestone:** F2.3 (Dataset Expansion Readiness)

---

## 1. Executive Notice & Scientific Integrity Premise

> [!IMPORTANT]
> The bounded 6-granule cohort acquired in Milestone F2.3 validates the multi-channel preprocessing pipeline, sensor cross-calibration, and relational database integrity. 
> **It is not, and must never be represented as, a sufficient training dataset for production deep learning models.**
> This report establishes the scientific rationale, statistical power requirements, and multi-scenario blueprints for expanding Vayumarg into a production-grade machine learning dataset (Milestone F2.4 and beyond).

---

## 2. Climatological & Meteorological Realities of the North Indian Ocean

Building a representative cyclone dataset for the North Indian Ocean (NIO) requires addressing fundamental meteorological properties:

### 2.1 Basin Asymmetry & Climatology
- **Bay of Bengal (BOB):** Accounts for approximately **$70\%$ to $75\%$** of all NIO cyclogenesis, peaking in the post-monsoon (October–December) and pre-monsoon (April–May) transitional seasons.
- **Arabian Sea (ARB):** Accounts for **$25\%$ to $30\%$** of storms. Historically fewer storms, but recent climate trends show increased rapid intensification and intense cyclones (e.g. BIPARJOY, TAUKTAE, MEKUNU).
- **Target Distribution:** Any robust ML dataset must maintain a stratified ratio of approximately **$2.5:1$** (BOB to ARB) to avoid severe geographical over-fitting.

### 2.2 Class Imbalance Across IMD Intensity Categories
In historical archives (1990–2024), cyclone intensity frequencies are heavily skewed toward weaker systems:
- Depression (D) / Deep Depression (DD): $\sim 45\%$ of all fixes.
- Cyclonic Storm (CS, 35–47 kts): $\sim 25\%$ of fixes.
- Severe Cyclonic Storm (SCS, 48–63 kts): $\sim 15\%$ of fixes.
- Very Severe Cyclonic Storm (VSCS, 64–89 kts): $\sim 10\%$ of fixes.
- Extremely Severe / Super Cyclonic Storm (ESCS $\ge 90\text{ kts}$, SuCS $\ge 120\text{ kts}$): $< 5\%$ of fixes.
- **Scientific Requirement:** Intentional over-sampling of ESCS and SuCS stages is mandatory to prevent regression models from suffering from central-tendency bias (under-predicting extreme peak winds).

### 2.3 Temporal Autocorrelation & Frame Independence
- Geostationary imagery acquired every 30 minutes exhibits massive temporal correlation. Two consecutive frames of the same cyclone 30 minutes apart share $\sim 98\%$ spatial structure.
- **Data Governance Invariant:** Splitting train, validation, and test sets by individual frames causes catastrophic data leakage. **All data splits must be partitioned strictly by unique Storm SID**.

---

## 3. Alternative Expansion Scenarios

| Attribute | Scenario 1: Prototype Cohort | Scenario 2: Balanced Decadal Cohort | Scenario 3: Comprehensive Foundation |
| :--- | :--- | :--- | :--- |
| **Objective** | Baseline Model Prototyping | SIH 2026 Competitive Benchmark | Operational Production Corpus |
| **Target Storms** | **10 storms** | **35 storms** (2018–2024) | **70 storms** (2014–2024) |
| **Basin Split** | 7 BOB / 3 ARB | 25 BOB / 10 ARB | 50 BOB / 20 ARB |
| **Sensors Covered** | INSAT-3DR, INSAT-3DS | INSAT-3DR, INSAT-3DS | INSAT-3D, 3DR, 3DS |
| **Raw Granules** | **60 granules** | **250 granules** | **1,000 granules** |
| **Raw Storage (L1B)** | $\sim 17.5\text{ GB}$ | $\sim 72.5\text{ GB}$ | $\sim 290.0\text{ GB}$ |
| **Processed Crop Storage**| $\sim 37\text{ MB}$ ($618\text{ KB/crop}$) | $\sim 155\text{ MB}$ | $\sim 620\text{ MB}$ |
| **IMD Synoptic Pairs** | $\sim 60$ samples | $\sim 250$ samples | $\sim 1,000$ samples |
| **Acquisition Time** | $\sim 2.5\text{ hours}$ | $\sim 10\text{ hours}$ (phased batches) | Dedicated batch worker |
| **Disk Headroom Needed** | $> 30\text{ GB}$ | $> 100\text{ GB}$ | Dedicated external SSD / NVMe |

---

## 4. Recommended Roadmap for Milestone F2.4

1. **Adopt Scenario 2 (Balanced Decadal Cohort):**
   - 35 storms from 2018 to 2024 provides 250 high-quality, authentic multi-channel crops synchronized with IMD best-track ground truth.
   - Captures all recent landmark cyclones: AMPHAN (SuCS), FANI (ESCS), BIPARJOY (ESCS), TAUKTAE (ESCS), REMAL (SCS), DANA (SCS), MICHAUNG (SCS), MOCHA (ESCS), ASANI (SCS).
2. **Selective Raw Asset Purging:**
   - Because raw L1B full disks require $\sim 280\text{ MB}$ each while extracted storm crops require only $\sim 618\text{ KB}$ ($0.22\%$ of raw size), storage can be dramatically optimized:
   - Once a raw granule is verified by SHA-256, its $800\text{ km}$ multi-channel crop extracted, and registered in the database, the raw full disk can be archived to secondary storage or deleted if local disk capacity is constrained, retaining the bit-perfect crop container.
3. **Execution Gating:**
   - Execute in bounded batches of 25 granules per run to respect MOSDAC server limits and network bandwidth.

