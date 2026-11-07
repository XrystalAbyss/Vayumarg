# VAYUMARG 3.0 — P1-DRIVE.3 FOUR-MODEL CHECKPOINT RESTORE RUNBOOK

**Document Version:** 1.0.0  
**Audit Date:** 7 November 2026  
**Auditor:** Backup & Disaster Recovery Architect & Information Security Engineer  
**Restoration Target:** Clean Windows 11 Workstation / Reconstructed Project Root  
**Drive Manifest Reference:** [`reports/v3/checkpoint_cloud_registry.json`](file:///C:/Users/astra/Desktop/Project/Vayumarg/reports/v3/checkpoint_cloud_registry.json)  

---

## 1. Safety Guardrails & Pre-Restoration Policies

1. **Pre-Staging Quarantine:** Downloads must **never** target the production model directory directly. All downloads are written to a temporary quarantine directory, where SHA-256 checksums are verified before atomic promotion.
2. **No Silent Overwrite:** If a checkpoint already exists at the destination, the restore script computes its SHA-256. If identical, the operation is skipped. If conflicting, the user must explicitly provide an `--overwrite` flag.
3. **Cryptographic Validation Invariant:**
   $$\text{SHA-256}(\text{Downloaded Checkpoint}) == \text{Authoritative Registry Hash}$$
   If a single bit differs, the restored file is deleted and quarantined immediately.

---

## 2. Checkpoint Cloud Reference Table

| Model Identity | Drive File ID | Target Project Path | Exact Size (Bytes) | Authoritative SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **`satellite_cnn_best`** | `1uM3hTiQX17JWLJClXJw_hhTm7J3PQnZD` | `models/vayumarg/vision/satellite_cnn_best.pt` | 135,432,053 | `2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865` |
| **`satellite_convlstm_best`** | `1QGklBkL4_FoIAmFMIeSWdLqYBQPQqpjK` | `models/vayumarg/vision/satellite_convlstm_best.pt` | 4,353,804 | `007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d` |
| **`track_gru_best`** | `1mFPoUhhSMJ0ZT6L8p7wYUIQjuJm28B0z` | `models/vayumarg/track_gru_best.pt` | 1,729,622 | `24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986` |
| **`track_hybrid_residual_best`** | `1sPtRSI8usMFE31SRwZaE8Bt8AGcuMhuV` | `models/vayumarg/track_hybrid_residual_best.pt` | 210,882 | `7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0` |

---

## 3. Automated Checkpoint Restore Script

The following self-contained Python script restores all four model checkpoints with pre-move quarantine and verification:

```python
"""Vayumarg 3.0 — Automated Checkpoint Restorer.

Downloads all four authorized checkpoints from private Google Drive, verifies SHA-256
in a temporary quarantine folder, and promotes them to the models directory.
"""

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

CHECKPOINTS = [
    {
        "id": "1uM3hTiQX17JWLJClXJw_hhTm7J3PQnZD",
        "name": "satellite_cnn_best.pt",
        "dest": Path("models/vayumarg/vision/satellite_cnn_best.pt"),
        "sha256": "2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865",
        "size": 135432053,
    },
    {
        "id": "1QGklBkL4_FoIAmFMIeSWdLqYBQPQqpjK",
        "name": "satellite_convlstm_best.pt",
        "dest": Path("models/vayumarg/vision/satellite_convlstm_best.pt"),
        "sha256": "007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d",
        "size": 4353804,
    },
    {
        "id": "1mFPoUhhSMJ0ZT6L8p7wYUIQjuJm28B0z",
        "name": "track_gru_best.pt",
        "dest": Path("models/vayumarg/track_gru_best.pt"),
        "sha256": "24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986",
        "size": 1729622,
    },
    {
        "id": "1sPtRSI8usMFE31SRwZaE8Bt8AGcuMhuV",
        "name": "track_hybrid_residual_best.pt",
        "dest": Path("models/vayumarg/track_hybrid_residual_best.pt"),
        "sha256": "7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0",
        "size": 210882,
    },
]

def compute_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def restore_all(overwrite: bool = False):
    print("=" * 80)
    print("VAYUMARG 3.0 — SECURE CHECKPOINT RESTORATION")
    print("=" * 80)

    for item in CHECKPOINTS:
        target = item["dest"]
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() and not overwrite:
            existing_hash = compute_sha256(target)
            if existing_hash == item["sha256"]:
                print(f"[SKIP] {item['name']} already exists and hash matches.")
                continue
            else:
                raise RuntimeError(
                    f"Conflict: {target} exists with different hash! Pass overwrite=True to replace."
                )

        print(f"\n[DOWNLOADING] {item['name']} (ID: {item['id']})...")
        with tempfile.TemporaryDirectory() as qdir:
            qfile = Path(qdir) / item["name"]
            cmd = ["cmd.exe", "/c", "gdrive", "readonly", "download", item["id"], "--out", str(qfile)]
            subprocess.run(cmd, check=True)

            assert qfile.exists(), f"Downloaded file missing: {qfile}"
            actual_size = qfile.stat().st_size
            actual_hash = compute_sha256(qfile)

            assert actual_size == item["size"], f"Size mismatch for {item['name']}!"
            assert actual_hash == item["sha256"], f"Checksum mismatch for {item['name']}!"

            # Atomic move from quarantine to target
            shutil.move(str(qfile), str(target))
            print(f"[VERIFIED & RESTORED] {target} ({actual_size} bytes)")

    print("\nAll four checkpoints restored and verified successfully.")

if __name__ == "__main__":
    restore_all(overwrite=False)
```

---

## 4. Post-Restoration Verification Protocol

After executing restoration on a clean machine:
1. Verify model registry reports `OPERATIONAL`:
   ```powershell
   .venv\Scripts\python.exe -c "
   from vayumarg.ml.registry import get_model_registry
   reg = get_model_registry()
   assert reg['status'] == 'OPERATIONAL'
   print('Model Registry Status:', reg['status'])
   "
   ```
2. Execute regression inference smoke tests:
   ```powershell
   .venv\Scripts\python.exe scripts/backup/verify_model_compatibility.py
   ```
3. Run the complete test suite:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/unit/test_model_registry.py -v
   ```

