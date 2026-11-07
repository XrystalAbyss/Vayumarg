# F0 Environment Discovery Report

**Project:** Vayumarg — AI/ML Decision-Support System for Tropical Cyclones  
**Milestone:** F0 — Scientific Data Foundation & Repository Bootstrap  
**Date:** November 1, 2026  
**Auditor:** Principal Scientific Software Architect & Database Lead  

---

## 1. Executive Summary

A comprehensive environment and infrastructure discovery was conducted on the host machine prior to initializing the foundational repository. The workspace was initially an empty directory without an existing Git repository, virtual environment, or prior source code. All relevant host subsystems, compilers, container runtimes, GPU drivers, and potential port conflicts were systematically evaluated, documented, and configured.

---

## 2. Detected Host Environment & Versions

| Subsystem / Tool | Detected Status | Version / Details | Operational Impact & Mitigation |
| :--- | :--- | :--- | :--- |
| **Operating System** | Active | Windows 11 Home Single Language (Build 10.0.26200, 64-bit) | Local development primary OS; requires PowerShell handling for execution policies and environment variables. |
| **Physical Memory (RAM)** | Active | 16.0 GB (16,457,592 KB visible, ~1.5 GB free at start) | Memory is adequate for database and local metadata operations. Large raw arrays must remain on disk outside memory. |
| **Storage (Disk C:)** | Active | 194.8 GB Free / 315.9 GB Used (NTFS) | Ample capacity for local PostgreSQL data volumes and interim artifacts. |
| **Python** | Detected | CPython 3.12.10 (`C:\Users\astra\AppData\Local\Python\pythoncore-3.12-64\python.exe`) | Used as the canonical runtime for Vayumarg. |
| **UV Package Manager** | Active | `uv 0.12.21 (7af826859 2026-09-29 x86_64-pc-windows-msvc)` | High-performance venv and dependency resolution tool. |
| **WSL2** | Detected / Repaired | WSL2 Kernel 6.18.54.1-microsoft-standard-WSL2 | Initial `Ubuntu` distribution had a missing VHDX file, preventing Docker startup. Default distribution was switched to `docker-desktop` via `wsl -s docker-desktop`, resolving engine launch. |
| **Docker Desktop** | Active / Running | Docker Server 29.8.2, Docker Compose v5.5.1 | Used to host canonical PostGIS service. Launched cleanly via interactive session explorer. |
| **PostgreSQL (Host)** | Active / Conflict | Native PostgreSQL 16 on PID 7572 bound to host port `5432` | Detected port contention. Docker PostGIS container remapped to host port `5433` (`5433:5432`) to prevent password authentication collisions. |
| **Docker PostGIS** | Active / Verified | `postgis/postgis:16-3.4` (PostGIS 3.4.3, GEOS 3.9.0, PROJ 7.2.1) | Canonical geospatial database provider. |
| **GPU / Acceleration** | Detected | NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM, Driver 617.14, CUDA 13.4) | Available for future model training milestones (F1+). |
| **Security / WDAC** | Active / Mitigated | Windows Defender Application Control / AppLocker blocks unsigned `.pyd` C-extensions | Resolved by setting `DISABLE_SQLALCHEMY_CEXT=1`, triggering SQLAlchemy 2's pure Python fallback engine. |

---

## 3. Key Architectural Decisions & Trade-Offs

1. **Port Remapping (`5433:5432`):**
   - *Discovery:* A pre-existing PostgreSQL service was running on port 5432 on the host machine.
   - *Decision:* Configured Docker Compose and application settings to expose the PostGIS container on port `5433`. This avoids touching or interfering with the user's host database while ensuring clean isolation.
2. **WSL2 Distro Switch:**
   - *Discovery:* Default WSL2 distro pointed to an unregistered Ubuntu mount disk.
   - *Decision:* Executed `wsl -s docker-desktop` to designate the active Docker Desktop VM as default, restoring Docker daemon connectivity.
3. **WDAC Pure-Python C-Extension Bypass:**
   - *Discovery:* Windows Defender Application Control blocked SQLAlchemy's compiled `_util_cy.pyd` DLL in the user's virtual environment.
   - *Decision:* Applied `DISABLE_SQLALCHEMY_CEXT=1` across the package configuration, Alembic environment, and CLI entry points.
4. **Relational / Array Separation:**
   - Relational metadata, storm tracks, quality issues, and asset manifests reside in PostgreSQL/PostGIS.
   - Multi-gigabyte satellite rasters (HDF5/NetCDF) and model checkpoint binaries are stored on filesystem/object storage and referenced strictly by URI and SHA-256 hash.

---

## 4. Risks & Mitigations

| Risk | Consequence | Mitigation Strategy |
| :--- | :--- | :--- |
| Accidental commit of secrets or large data | Repository bloat and credential compromise | Strict `.gitignore` patterns prohibiting `.env`, raw data, HDF5, NetCDF, model checkpoints, and database dumps. |
| Unscientific wind speed conflation | Invalid ML models and degraded forecast skill | Data contract enforces agency-specific wind averaging periods (IMD 3-min vs JTWC 1-min) without arbitrary conversion. |
| Accidental Git commits | Violation of project preservation policy | Git initialized locally; no automated commits or remote pushes executed without explicit project-owner instruction. |

