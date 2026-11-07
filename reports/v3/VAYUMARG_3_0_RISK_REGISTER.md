# VAYUMARG 3.0 — SCIENTIFIC & TECHNICAL RISK REGISTER

**Classification:** Project Risk Assessment & Mitigation Architecture  
**Date:** 7 November 2026  
**Auditor:** Independent Validation & Reproducibility Auditor  
**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  

---

## 1. Risk Matrix Overview

Risks are categorized across three operational domains:
1. **Technical & Engineering Risks (T)**
2. **Scientific & Methodological Risks (S)**
3. **Operational, Legal & Data Governance Risks (G)**

Each risk is evaluated by Probability (1–5) and Impact (1–5), yielding a Risk Severity Score ($\text{Score} = P \times I$):
- **High Severity (15–25):** Critical attention; must be mitigated before Phase P1 execution.
- **Medium Severity (8–14):** Active mitigation required during implementation sprints.
- **Low Severity (1–7):** Monitor during periodic milestone reviews.

---

## 2. Risk Register Ledger

| ID | Category | Risk Description | Prob (1-5) | Imp (1-5) | Score | Mitigation Strategy & Controls | Residual Risk | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-T01** | Technical | **Untracked Zero-Commit Repository State:** Local directory has no Git commits; any file deletion or overwriting is unrecoverable. | 5 | 5 | **25 (HIGH)** | Immediately execute baseline freeze commit and tag `v2.2.3-freeze`. Create automated backup zip before any refactoring. | LOW (1) | Systems Lead |
| **RSK-S01** | Scientific | **Cross-Sensor Domain Transfer Collapse:** ResNet-18 trained on GOES (10.3 µm) produces inaccurate intensity rankings on INSAT (10.8 µm). | 4 | 4 | **16 (HIGH)** | Restrict model status to `VERIFIED_EXPERIMENTAL`. Display mandatory transfer limitation disclaimers. Prioritize native INSAT fine-tuning. | MED (8) | ML Research Lead |
| **RSK-S02** | Scientific | **Retrospective Reanalysis Look-Ahead Leakage:** Using ERA5 reanalysis fields as if they were real-time forecast fields available at issue time. | 4 | 4 | **16 (HIGH)** | Restrict reanalysis to retrospective diagnostic baselines. Use only operational archived GFS forecast cycles for forward issue-time simulations. | LOW (4) | Meteorologist |
| **RSK-T02** | Technical | **PostgreSQL Port 5432/5433 Collision:** Developers or test runners encounter connection refusal when Docker maps to 5433 while scripts look for 5432. | 4 | 3 | **12 (MED)** | Standardize on 5433 in `.env.example`, `config.py`, and test fixtures. Maintain seamless fallback to `data/demo_cache/`. | LOW (3) | Software Architect |
| **RSK-S03** | Scientific | **Model Selection Bias via Test Set Peeking:** Iterative hyperparameter tuning on the test set invalidates reported accuracy. | 4 | 3 | **12 (MED)** | Enforce strict Three-Tier data partitioning (Train / Dev-Val / Sequestered Confirmatory Test). Sequester Tier 3 with cryptographic verification. | LOW (3) | Validation Auditor |
| **RSK-G01** | Governance | **Redissemination Restrictions on Raw MOSDAC HDF5s:** Publishing multi-gigabyte ISRO raw satellite archives on public GitHub could violate data terms. | 3 | 4 | **12 (MED)** | Never commit raw HDF5 files to Git (`.gitignore` enforcement). Distribute only derived, calibrated $201 \times 201$ scientific crops and analytical manifests. | LOW (4) | Data Engineer |
| **RSK-S04** | Scientific | **Conflation of IMD (3-min) and JTWC (1-min) Wind Standards:** Misleading users by converting 1-min predictions with universal 0.88 scalar factors. | 3 | 4 | **12 (MED)** | Completely eliminate universal conversion factors. Segregate 1-min and 3-min fields across APIs, types, and UI panels. | LOW (2) | Meteorologist |
| **RSK-T03** | Technical | **CUDA / CPU Dependency Fragmentation:** PyTorch checkpoint loading failure on systems without NVIDIA GPUs. | 3 | 3 | **9 (MED)** | Enforce `map_location=device` on all `torch.load` calls. Include automated CPU-fallback smoke tests in CI suite. | LOW (3) | ML Engineer |
| **RSK-G02** | Governance | **Absence of Ground-Truth Reconnaissance Aircraft:** North Indian Ocean cyclones lack direct dropsonde / flight-level reconnaissance data. | 5 | 2 | **10 (MED)** | Acknowledge that best-track wind estimates carry an inherent $\pm 10\text{--}15\text{ kt}$ subjective Dvorak uncertainty envelope. Frame AI accuracy within this empirical envelope. | MED (8) | Meteorologist |

---

## 3. High-Priority Pre-P1 Action Plan

Before initiating Phase P1 development:
1. **Action 1 (Mitigate RSK-T01):** Create local `v2.2.3-freeze` commit and tagged archive.
2. **Action 2 (Mitigate RSK-T02):** Update `tests/integration/test_forecast_engine_db.py` to accept `canonical_sid` alongside `storm_sid` to restore 100% test passing status.
3. **Action 3 (Mitigate RSK-G01):** Ensure `.gitignore` continues to block `*.h5`, `*.tar.gz`, and raw data directories from Git commits.

