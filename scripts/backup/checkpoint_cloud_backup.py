"""Vayumarg 3.0 — P1-DRIVE.3 Checkpoint Preservation & Verification Engine.

Performs authenticated preflight checks, uploads the four authorized model checkpoints to their
designated Google Drive subfolders, executes full bitwise readback downloads with SHA-256 verification,
validates zero local file mutation, and generates versioned cloud checkpoint manifests.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(r"C:\Users\astra\Desktop\Project\Vayumarg")
ROOT_FOLDER_ID = "18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth"
ACCOUNT = "goyalishaan@gmail.com"

os.environ["AGY_ACCOUNT"] = ACCOUNT

MODELS_CONFIG = [
    {
        "model_id": "satellite_cnn_best",
        "relative_path": "models/vayumarg/vision/satellite_cnn_best.pt",
        "parent_folder_id": "1FlUO_w-G-SkwWOZvmq0zS9ELWSqqsftd",
        "parent_folder_name": "03_Trained_Models/Satellite_CNN",
        "expected_size": 135432053,
        "expected_hash": "2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865",
        "architecture": "ResNet18-IR-SingleChannel",
        "dataset_lineage": "NASA Tropical Cyclone Wind Estimation Competition (GOES-16/17 Band 13 @ 10.3 µm, 2,500 images across 25 storm IDs)",
        "preprocessing_contract": "Single-channel infrared brightness temperature crop, resized to 224x224, normalized to [0, 1]",
        "input_tensor_shape": [1, 1, 224, 224],
        "output_spec": "Scalar 1D sustained wind speed in knots (1-minute average)",
        "evaluation_reference": "reports/ml/CNN_TRAINING.md",
    },
    {
        "model_id": "satellite_convlstm_best",
        "relative_path": "models/vayumarg/vision/satellite_convlstm_best.pt",
        "parent_folder_id": "1cEZ3nyXF9V2oHsVDEnQuyaxiHyROUUCt",
        "parent_folder_name": "03_Trained_Models/Satellite_ConvLSTM",
        "expected_size": 4353804,
        "expected_hash": "007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d",
        "architecture": "CycloneConvLSTM-32-64",
        "dataset_lineage": "NASA Tropical Cyclone Wind Estimation Competition sequential temporal sequences (3 frames @ 3-hour delta)",
        "preprocessing_contract": "Temporal sequence of 3 infrared frames, resized to 128x128, normalized to [0, 1]",
        "input_tensor_shape": [1, 3, 1, 128, 128],
        "output_spec": "Scalar 1D sustained wind speed in knots (1-minute average)",
        "evaluation_reference": "reports/ml/CONVLSTM_TRAINING.md",
    },
    {
        "model_id": "track_gru_best",
        "relative_path": "models/vayumarg/track_gru_best.pt",
        "parent_folder_id": "1KHmwAFjwzdofU_F9vtBdvBudxSHplugz",
        "parent_folder_name": "03_Trained_Models/Track_GRU",
        "expected_size": 1729622,
        "expected_hash": "24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986",
        "architecture": "VayumargTrackGRU (2-layer GRU, 96 hidden units)",
        "dataset_lineage": "NOAA IBTrACS v04r01 North Indian Ocean historical tracks (1982-2024, 6-hourly observations)",
        "preprocessing_contract": "8-step historical trajectory sequence with 10 kinematic features (lat, lon, speed, heading, pressure, etc.)",
        "input_tensor_shape": [1, 8, 10],
        "output_spec": "Multi-horizon displacement vectors at +6h, +12h, and +24h forecast horizons",
        "evaluation_reference": "reports/v3/P0_SCIENTIFIC_MODEL_BASELINE.md",
    },
    {
        "model_id": "track_hybrid_residual_best",
        "relative_path": "models/vayumarg/track_hybrid_residual_best.pt",
        "parent_folder_id": "16Em3C-adxH--TqZndCvqPzBWdi0ocPfE",
        "parent_folder_name": "03_Trained_Models/Hybrid_Residual",
        "expected_size": 210882,
        "expected_hash": "7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0",
        "architecture": "HybridResidualModel (Geodesic Kinematic Baseline + MLP Residual Correction)",
        "dataset_lineage": "NOAA IBTrACS v04r01 North Indian Ocean historical tracks with spherical geodesic residual errors",
        "preprocessing_contract": "Kinematic feature vector combining geodesic extrapolation and atmospheric state",
        "input_tensor_shape": [1, 8, 10],
        "output_spec": "Residual spatial corrections to Great-Circle geodesic trajectory predictions",
        "evaluation_reference": "reports/v3/P0_SCIENTIFIC_MODEL_BASELINE.md",
    },
]

MANIFESTS_FOLDER_ID = "1PwL6jQ-GKh1CKSXH0VtbUz1bSahaUAu0"

def run_cmd(args: list[str], max_retries: int = 3, retry_delay: float = 3.0) -> str:
    full_cmd = ["cmd.exe", "/c"] + args
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            res = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(retry_delay)
    raise last_err

def run_gdrive_json(args: list[str]) -> dict | list:
    out = run_cmd(["gdrive"] + args + ["--json"])
    if not out:
        return {}
    return json.loads(out)

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def parse_id(output: str) -> str | None:
    m = re.search(r"\(ID:\s*([a-zA-Z0-9_-]+)\)", output)
    if m:
        return m.group(1)
    return None

def main():
    print("=" * 80)
    print("VAYUMARG 3.0 — P1-DRIVE.3 FOUR-MODEL CHECKPOINT PRESERVATION & ACCEPTANCE")
    print(f"Target Google Drive Root: {ROOT_FOLDER_ID}")
    print(f"Authenticated Account:    {ACCOUNT}")
    print("=" * 80)

    # Preflight Checkpoints Validation
    local_state_before = {}
    for m in MODELS_CONFIG:
        p = PROJECT_ROOT / m["relative_path"]
        assert p.exists(), f"Source checkpoint missing: {p}"
        sz = p.stat().st_size
        mtime = p.stat().st_mtime
        assert sz == m["expected_size"], f"Size mismatch for {p.name}"
        h = compute_sha256(p)
        assert h == m["expected_hash"], f"Hash mismatch for {p.name}"
        local_state_before[m["model_id"]] = {"mtime": mtime, "size": sz, "hash": h}
        print(f"  [OK] Local Preflight: {p.name} ({sz} bytes, SHA-256: {h[:16]}...)")

    upload_results = []

    for m in MODELS_CONFIG:
        local_path = PROJECT_ROOT / m["relative_path"]
        filename = local_path.name
        print(f"\n--- Processing {filename} ({local_path.stat().st_size} bytes) ---")
        
        # Check if already uploaded and valid
        existing_items = run_gdrive_json(["readonly", "ls", m["parent_folder_id"]])
        existing_items = existing_items if isinstance(existing_items, list) else []
        file_id = None
        for it in existing_items:
            if it.get("name") == filename and int(it.get("size", -1)) == m["expected_size"]:
                file_id = it.get("id")
                print(f"  [ALREADY PRESENT] Verified existing remote copy: {filename} (ID: {file_id})")
                t_upload_elapsed = 0.0
                break

        if not file_id:
            print(f"  Uploading {filename} to {m['parent_folder_name']} ({m['parent_folder_id']})...")
            t_upload_start = time.perf_counter()
            out = run_cmd(["gdrive", "mutate", "upload", str(local_path), "--parent", m["parent_folder_id"]])
            t_upload_elapsed = time.perf_counter() - t_upload_start
            file_id = parse_id(out)
            assert file_id, f"Failed to parse uploaded file ID for {filename}. Output: {out}"
            print(f"  [UPLOAD SUCCESS] File ID: {file_id} (Elapsed: {t_upload_elapsed:.2f}s)")

        # Verify Remote Metadata
        meta = run_gdrive_json(["readonly", "info", file_id])
        assert meta.get("id") == file_id, "Metadata ID mismatch!"
        assert meta.get("name") == filename, f"Remote filename mismatch: {meta.get('name')}"
        assert m["parent_folder_id"] in meta.get("parents", []), f"Remote parent mismatch: {meta.get('parents')}"
        remote_size = int(meta.get("size", -1))
        assert remote_size == m["expected_size"], f"Remote size mismatch"
        print(f"  [METADATA CONFIRMED] Name: {meta.get('name')}, Size: {remote_size} bytes")

        # Download & Bitwise SHA-256 Verification
        print(f"  Executing readback verification for {filename}...")
        with tempfile.TemporaryDirectory(prefix=f"vayumarg_chk_{m['model_id']}_") as tmpdir:
            dest_download = Path(tmpdir) / filename
            t_down_start = time.perf_counter()
            run_cmd(["gdrive", "readonly", "download", file_id, "--out", str(dest_download)], max_retries=3, retry_delay=5.0)
            t_down_elapsed = time.perf_counter() - t_down_start
            
            assert dest_download.exists(), "Downloaded file missing!"
            restored_size = dest_download.stat().st_size
            restored_hash = compute_sha256(dest_download)
            
            assert restored_size == m["expected_size"], "Byte count mismatch!"
            assert restored_hash == m["expected_hash"], f"SHA-256 mismatch for {filename}!"
            print(f"  [DOWNLOAD VERIFIED] {restored_size} bytes, SHA-256 matches: {restored_hash[:16]}... (Elapsed: {t_down_elapsed:.2f}s)")
            print(f"  >>> VERIFIED_BYTE_FOR_BYTE CONFIRMED FOR {filename} <<<")

        # Confirm zero mutation on local original
        assert local_path.stat().st_size == local_state_before[m["model_id"]]["size"]
        assert compute_sha256(local_path) == local_state_before[m["model_id"]]["hash"]
        print(f"  [LOCAL INTACT] Original {filename} remains completely unaltered.")

        upload_results.append({
            "model_id": m["model_id"],
            "filename": filename,
            "local_relative_path": m["relative_path"],
            "drive_file_id": file_id,
            "parent_folder_id": m["parent_folder_id"],
            "parent_folder_name": m["parent_folder_name"],
            "file_size_bytes": m["expected_size"],
            "sha256": m["expected_hash"],
            "architecture": m["architecture"],
            "dataset_lineage": m["dataset_lineage"],
            "preprocessing_contract": m["preprocessing_contract"],
            "input_tensor_shape": m["input_tensor_shape"],
            "output_spec": m["output_spec"],
            "evaluation_reference": m["evaluation_reference"],
            "upload_duration_sec": round(t_upload_elapsed, 2),
            "download_duration_sec": round(t_down_elapsed, 2),
            "verification_status": "VERIFIED_BYTE_FOR_BYTE",
            "backup_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    # Save Cloud Manifest
    manifest_path = PROJECT_ROOT / "reports" / "v3" / "checkpoint_cloud_registry.json"
    manifest_data = {
        "registry_title": "Vayumarg 3.0 Four-Model Private Cloud Checkpoint Registry",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_folder_id": ROOT_FOLDER_ID,
        "authenticated_account": ACCOUNT,
        "total_checkpoints": len(upload_results),
        "total_volume_bytes": sum(x["file_size_bytes"] for x in upload_results),
        "total_volume_mib": round(sum(x["file_size_bytes"] for x in upload_results) / (1024*1024), 2),
        "verification_verdict": "VERIFIED_BYTE_FOR_BYTE",
        "checkpoints": upload_results,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"\n[OK] Saved local manifest to {manifest_path}")

    # Upload manifest copy to 03_Trained_Models/Model_Manifests
    print(f"\nUploading manifest copy to Model_Manifests folder ({MANIFESTS_FOLDER_ID})...")
    out_m = run_cmd(["gdrive", "mutate", "upload", str(manifest_path), "--parent", MANIFESTS_FOLDER_ID])
    manifest_file_id = parse_id(out_m)
    assert manifest_file_id, f"Failed to upload manifest: {out_m}"
    print(f"  [OK] Manifest uploaded to Drive. Remote ID: {manifest_file_id}")
    
    # Readback verify manifest
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_m = Path(tmpdir) / "checkpoint_cloud_registry.json"
        run_cmd(["gdrive", "readonly", "download", manifest_file_id, "--out", str(dest_m)])
        assert dest_m.exists()
        assert compute_sha256(dest_m) == compute_sha256(manifest_path)
        print("  [OK] Manifest readback 100% verified bit-for-bit.")

    print("\n" + "=" * 80)
    print("ALL FOUR MODEL CHECKPOINTS SUCCESSFULLY PRESERVED & 100% VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
