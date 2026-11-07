# Milestone F2.4: Download Reliability & Recovery Architecture

**Repository:** `C:\Users\astra\Desktop\Project\Vayumarg`  
**Milestone:** F2.4 — Download Recovery Architecture  
**Author:** Principal Satellite Data Engineer & Secure Network Systems Engineer  
**Date:** 2026-11-01  

---

## 1. Failure Analysis of Prior Milestones

During Milestone F2.3, batch acquisition of 6 MOSDAC granules failed due to three architectural vulnerabilities in the baseline client implementation:

1. **Vendor Script Deletion of Partials:** The official vendor script (`mdapi.py`) explicitly executed `os.remove(tmp_file_path)` at the start of any download attempt where an incomplete `.part` file existed. Any socket interruption resulted in total loss of progress.
2. **Fixed Low Socket Read Timeout:** Initial timeout configurations were constrained to 15 seconds connection and 60–120 seconds read. Under high-latency MOSDAC server load, 280–400 MB file streams stalled and timed out.
3. **Absence of HTTP Range Headers:** Transfers were issued unconditionally without requesting byte ranges or verifying server resume capability.

---

## 2. Recovery Engineering & Upgrades in F2.4

To resolve these defects permanently, Milestone F2.4 implemented the following architectural enhancements:

### 2.1 FaultTolerantMOSDACDownloader Engine
- Implemented in `src/vayumarg/satellite/mosdac_recovery.py`.
- **Capability Probing:** Authenticated, non-destructive Range capability probe (`probe_range_capability`) validating HTTP 206 responses, `Content-Range` byte alignment, and total object consistency.
- **Resumption with Fallback:** If server supports Range, automatically requests `Range: bytes=<existing_bytes>-` and appends missing segments to `.part`. If server returns 200, cleanly restarts into a temporary staging file without corruption.
- **Credential-Free Metadata Sidecars:** Retains `<filename>.part.meta.json` tracking total size, bytes downloaded, ETag, and last modified timestamps without storing credentials or auth tokens.
- **Atomic Promotion:** Canonical destination paths (`.h5`) are written strictly via atomic filesystem rename (`os.replace`) upon complete stream termination and valid HDF5 verification.
- **Quarantine Gating:** Incomplete `.part` files are strictly quarantined from scientific observation tables in PostgreSQL.

---

## 3. Storage Headroom & Safety Reserve
- **Drive C Free Capacity:** 59.48 GB.
- **Minimum Safety Headroom:** 5.0 GB hard reserve enforced by `check_disk_headroom()`.
- **Option A Acquisition Budget:** 18 granules $\approx 5.4\text{ GB}$ (Maximum 9.08% of available disk space).
- **User Privacy:** Mortal Kombat 11 gaming installation accounted for disk space shift; zero file scanning or directory traversal was performed outside `C:\Users\astra\Desktop\Project\Vayumarg`.

