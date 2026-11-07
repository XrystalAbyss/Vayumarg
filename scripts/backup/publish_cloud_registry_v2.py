"""Vayumarg 3.0 — Corrected Cloud Checkpoint Registry (v2.0.0).

Corrects all preprocessing specifications, input tensor shapes, temporal cadence records,
feature definitions, and transfer timings to match verified source code implementations.
"""

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\astra\Desktop\Project\Vayumarg")
ROOT_FOLDER_ID = "18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth"
MANIFESTS_FOLDER_ID = "1PwL6jQ-GKh1CKSXH0VtbUz1bSahaUAu0"
ACCOUNT = "goyalishaan@gmail.com"

os.environ["AGY_ACCOUNT"] = ACCOUNT

REGISTRY_V2 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "registry_version": "2.0.0",
    "registry_title": "Vayumarg 3.0 Authoritative Cloud Checkpoint Registry",
    "last_updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "root_folder_id": ROOT_FOLDER_ID,
    "authenticated_account": ACCOUNT,
    "total_checkpoints": 4,
    "total_volume_bytes": 141726361,
    "total_volume_mib": 135.16,
    "total_volume_mb": 141.73,
    "verification_verdict": "VERIFIED_BYTE_FOR_BYTE",
    "checkpoints": [
        {
            "model_id": "satellite_cnn_best",
            "filename": "satellite_cnn_best.pt",
            "local_relative_path": "models/vayumarg/vision/satellite_cnn_best.pt",
            "drive_file_id": "1uM3hTiQX17JWLJClXJw_hhTm7J3PQnZD",
            "parent_folder_id": "1FlUO_w-G-SkwWOZvmq0zS9ELWSqqsftd",
            "parent_folder_name": "03_Trained_Models/Satellite_CNN",
            "file_size_bytes": 135432053,
            "sha256": "2613a63cac762151555531c2b9e5d0f3832976cac2c452d296f42d5e94644865",
            "architecture": "ResNet18-IR-SingleChannel",
            "dataset_lineage": "NASA Tropical Cyclone Wind Estimation Competition (GOES-16/17 Band 13 @ 10.3 µm, Himawari-8 Band 13 @ 10.4 µm; 2,500 images across 25 storm IDs; distinct from TCIR)",
            "preprocessing_contract": "Single-channel infrared brightness temperature crop, resized to 128x128 px, normalized with mean=[0.45] and std=[0.22]",
            "input_tensor_shape": [1, 1, 128, 128],
            "output_spec": "Scalar 1-minute sustained wind speed in knots (Huber regression) and 6-class auxiliary category logits",
            "evaluation_reference": "reports/ml/CNN_TRAINING.md",
            "upload_duration_sec": 139.21,
            "download_duration_sec": 248.54,
            "verification_status": "VERIFIED_BYTE_FOR_BYTE",
            "backup_timestamp_utc": "2026-11-07T10:59:34Z"
        },
        {
            "model_id": "satellite_convlstm_best",
            "filename": "satellite_convlstm_best.pt",
            "local_relative_path": "models/vayumarg/vision/satellite_convlstm_best.pt",
            "drive_file_id": "1QGklBkL4_FoIAmFMIeSWdLqYBQPQqpjK",
            "parent_folder_id": "1cEZ3nyXF9V2oHsVDEnQuyaxiHyROUUCt",
            "parent_folder_name": "03_Trained_Models/Satellite_ConvLSTM",
            "file_size_bytes": 4353804,
            "sha256": "007aa5233373dbcc108c4b6518201d9092a0150e6751eb6ca0144090a64b680d",
            "architecture": "CycloneConvLSTM-32-64 (2-layer recurrent spatiotemporal network)",
            "dataset_lineage": "NASA Tropical Cyclone Wind Estimation Competition sequential temporal sequences (2,425 chronological sequences across 25 storm IDs; distinct from TCIR)",
            "preprocessing_contract": "Chronological sequence of T=3 infrared frames, resized to 64x64 px, normalized with mean=[0.45] and std=[0.22] (irregular satellite observation intervals matching capture timestamps)",
            "input_tensor_shape": [1, 3, 1, 64, 64],
            "output_spec": "Scalar 1-minute sustained future wind intensity (knots) and normalized next-frame infrared imagery (1, 1, 64, 64)",
            "evaluation_reference": "reports/ml/CONVLSTM_TRAINING.md",
            "upload_duration_sec": 8.42,
            "download_duration_sec": 10.06,
            "verification_status": "VERIFIED_BYTE_FOR_BYTE",
            "backup_timestamp_utc": "2026-11-07T11:13:52Z"
        },
        {
            "model_id": "track_gru_best",
            "filename": "track_gru_best.pt",
            "local_relative_path": "models/vayumarg/track_gru_best.pt",
            "drive_file_id": "1mFPoUhhSMJ0ZT6L8p7wYUIQjuJm28B0z",
            "parent_folder_id": "1KHmwAFjwzdofU_F9vtBdvBudxSHplugz",
            "parent_folder_name": "03_Trained_Models/Track_GRU",
            "file_size_bytes": 1729622,
            "sha256": "24d4788f8ebe2b02e0e9a8d7c9b7715f6fa20a33cdae1a29c321f7e4e48b6986",
            "architecture": "VayumargTrackGRU (2-layer GRU, 96 hidden units, temporal self-attention pooling)",
            "dataset_lineage": "NOAA IBTrACS v04r01 North Indian Ocean historical tracks (1982-2024, 3-hourly sliding windows, 6h/12h/24h target horizons)",
            "preprocessing_contract": "8-step historical trajectory sequence (24h observation window at 3h cadence) with 10 kinematic features: normalized lat, lon, dx, dy, translational speed, bearing sine/cosine, wind speed, delta wind, and temporal progression index",
            "input_tensor_shape": [1, 8, 10],
            "output_spec": "Multi-horizon displacement vectors (dx, dy) in km and future sustained wind speeds at +6h, +12h, and +24h horizons",
            "evaluation_reference": "reports/v3/P0_SCIENTIFIC_MODEL_BASELINE.md",
            "upload_duration_sec": 28.21,
            "download_duration_sec": 7.86,
            "verification_status": "VERIFIED_BYTE_FOR_BYTE",
            "backup_timestamp_utc": "2026-11-07T11:14:30Z"
        },
        {
            "model_id": "track_hybrid_residual_best",
            "filename": "track_hybrid_residual_best.pt",
            "local_relative_path": "models/vayumarg/track_hybrid_residual_best.pt",
            "drive_file_id": "1sPtRSI8usMFE31SRwZaE8Bt8AGcuMhuV",
            "parent_folder_id": "16Em3C-adxH--TqZndCvqPzBWdi0ocPfE",
            "parent_folder_name": "03_Trained_Models/Hybrid_Residual",
            "file_size_bytes": 210882,
            "sha256": "7f23988c92e86b3c1a2ca170ffe2c53f897ef1d6484ffff2c5a83230258186a0",
            "architecture": "VayumargHybridTrackModel (2-layer GRU with hidden_size=64, Great-Circle Geodesic Kinematic Baseline + Bounded MLP Residual Heads)",
            "dataset_lineage": "NOAA IBTrACS v04r01 North Indian Ocean historical tracks with spherical geodesic residual errors (1982-2024; strictly kinematic, zero atmospheric GFS/ERA5 features)",
            "preprocessing_contract": "8-step historical trajectory sequence (24h observation window at 3h cadence) with 10 kinematic features paired with baseline geodesic displacement tensor",
            "input_tensor_shape": [1, 8, 10],
            "output_spec": "Hybrid displacement vectors combining geodesic kinematic baseline with learned residual corrections (bounded tanh) at +6h, +12h, and +24h",
            "evaluation_reference": "reports/v3/P0_SCIENTIFIC_MODEL_BASELINE.md",
            "upload_duration_sec": 3.77,
            "download_duration_sec": 2.52,
            "verification_status": "VERIFIED_BYTE_FOR_BYTE",
            "backup_timestamp_utc": "2026-11-07T11:14:38Z"
        }
    ]
}

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    print("=" * 80)
    print("VAYUMARG 3.0 — GENERATE & UPLOAD CORRECTED CLOUD REGISTRY V2")
    print("=" * 80)

    # 1. Save locally as checkpoint_cloud_registry_v2.json
    out_path = PROJECT_ROOT / "reports" / "v3" / "checkpoint_cloud_registry_v2.json"
    content = json.dumps(REGISTRY_V2, indent=2)
    out_path.write_text(content, encoding="utf-8")
    local_size = out_path.stat().st_size
    local_hash = compute_sha256(out_path)
    print(f"Created local {out_path.name}: {local_size} bytes, SHA-256: {local_hash}")

    # 2. Upload to Google Drive Model_Manifests folder (1PwL6jQ-GKh1CKSXH0VtbUz1bSahaUAu0)
    print(f"Uploading {out_path.name} to Drive Model_Manifests folder ({MANIFESTS_FOLDER_ID})...")
    cmd = ["cmd.exe", "/c", "gdrive", "mutate", "upload", str(out_path), "--parent", MANIFESTS_FOLDER_ID]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out_text = res.stdout.strip()
    print("Upload result:", out_text)

    # Parse file ID
    import re
    m = re.search(r"\(ID:\s*([a-zA-Z0-9_-]+)\)", out_text)
    assert m, f"Could not parse file ID from {out_text}"
    v2_file_id = m.group(1)
    print(f"[OK] New v2 manifest uploaded. Remote File ID: {v2_file_id}")

    # 3. Readback Verification into temporary directory
    print("Performing readback verification of newly uploaded manifest...")
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_readback = Path(tmpdir) / "checkpoint_cloud_registry_v2.json"
        cmd_dl = ["cmd.exe", "/c", "gdrive", "readonly", "download", v2_file_id, "--out", str(dest_readback)]
        subprocess.run(cmd_dl, capture_output=True, text=True, check=True)
        assert dest_readback.exists(), "Readback download missing!"
        readback_size = dest_readback.stat().st_size
        readback_hash = compute_sha256(dest_readback)
        print(f"Readback Size: {readback_size} bytes (Expected: {local_size})")
        print(f"Readback Hash: {readback_hash}")
        assert readback_size == local_size, "Readback size mismatch!"
        assert readback_hash == local_hash, "Readback hash mismatch!"
        print(">>> 100% BITWISE VERIFICATION CONFIRMED FOR NEW MANIFEST V2 <<<")

if __name__ == "__main__":
    main()

