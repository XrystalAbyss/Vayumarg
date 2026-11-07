"""Vayumarg 3.0 — Idempotent Google Drive Workspace Initializer & Transfer Verifier.

Initializes the canonical scientific folder hierarchy under root folder 18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth,
uploads connection test artifact, performs readback validation, and executes Tier 1 foundation transfers.
"""

import json
import os
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path

ROOT_FOLDER_ID = "18Yvd7LFeNSKWA3ieGpLNk8-lzMf62tth"
ACCOUNT = "goyalishaan@gmail.com"
PROJECT_ROOT = Path(r"C:\Users\astra\Desktop\Project\Vayumarg")

# Ensure environment has AGY_ACCOUNT set
os.environ["AGY_ACCOUNT"] = ACCOUNT

def run_gdrive(cmd_args: list[str]) -> dict | list | str:
    """Run gdrive CLI and parse JSON output."""
    full_cmd = ["gdrive"] + cmd_args + ["--json"]
    res = subprocess.run(full_cmd, capture_output=True, text=True, check=True, shell=True)
    out = res.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out

def get_children(folder_id: str) -> dict[str, str]:
    """Get mapping of name -> folder_id for folders under parent."""
    items = run_gdrive(["readonly", "ls", folder_id])
    folder_map = {}
    if isinstance(items, list):
        for item in items:
            if item.get("mimeType") == "application/vnd.google-apps.folder":
                folder_map[item.get("name")] = item.get("id")
    return folder_map

def ensure_folder(name: str, parent_id: str) -> str:
    """Idempotently create folder if missing, return folder ID."""
    children = get_children(parent_id)
    if name in children:
        print(f"  [EXISTS] {name} -> {children[name]}")
        return children[name]
    
    print(f"  [CREATING] {name} under parent {parent_id}...")
    res = run_gdrive(["mutate", "mkdir", name, "--parent", parent_id])
    folder_id = res.get("id") if isinstance(res, dict) else None
    if not folder_id:
        # Check again via ls
        children = get_children(parent_id)
        folder_id = children.get(name)
    assert folder_id, f"Failed to obtain folder ID for {name}"
    print(f"  [CREATED]  {name} -> {folder_id}")
    return folder_id

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    print("=" * 80)
    print("VAYUMARG 3.0 — GOOGLE DRIVE WORKSPACE INITIALIZATION & VERIFICATION")
    print(f"Root Folder ID: {ROOT_FOLDER_ID}")
    print(f"Authenticated Account: {ACCOUNT}")
    print("=" * 80)

    # 1. Verify Root Folder
    print("\n[Step 1] Verifying Root Folder Metadata...")
    root_info = run_gdrive(["readonly", "info", ROOT_FOLDER_ID])
    assert root_info.get("name") == "Vayumarg", f"Unexpected name: {root_info.get('name')}"
    assert root_info.get("id") == ROOT_FOLDER_ID, "Root folder ID mismatch!"
    print(f"Root Verified: {root_info.get('name')} ({root_info.get('id')})")

    # 2. Build Hierarchy
    print("\n[Step 2] Establishing Idempotent Folder Hierarchy...")
    registry = {"_root": ROOT_FOLDER_ID}

    primary_folders = [
        "01_Project_Management",
        "02_Scientific_Datasets",
        "03_Trained_Models",
        "04_Research_Experiments",
        "05_Project_Documentation",
        "06_Backups",
        "07_Team_Collaboration",
    ]

    for f_name in primary_folders:
        f_id = ensure_folder(f_name, ROOT_FOLDER_ID)
        registry[f_name] = {"id": f_id, "parent": ROOT_FOLDER_ID, "children": {}}

    # Subfolders of 02_Scientific_Datasets
    sub_02 = [
        "NASA_Tropical_Cyclone",
        "NOAA_IBTrACS",
        "ISRO_INSAT",
        "Environmental_Data",
        "Dataset_Manifests",
    ]
    print("\nCreating subfolders under 02_Scientific_Datasets...")
    for s_name in sub_02:
        s_id = ensure_folder(s_name, registry["02_Scientific_Datasets"]["id"])
        registry["02_Scientific_Datasets"]["children"][s_name] = s_id

    # Subfolders of 03_Trained_Models
    sub_03 = [
        "Satellite_CNN",
        "Satellite_ConvLSTM",
        "Track_GRU",
        "Hybrid_Residual",
        "Model_Manifests",
    ]
    print("\nCreating subfolders under 03_Trained_Models...")
    for s_name in sub_03:
        s_id = ensure_folder(s_name, registry["03_Trained_Models"]["id"])
        registry["03_Trained_Models"]["children"][s_name] = s_id

    # Subfolders of 04_Research_Experiments
    sub_04 = [
        "Module_A",
        "Module_B",
        "Evaluation_Ledgers",
        "Research_Plots",
        "Experiment_Manifests",
    ]
    print("\nCreating subfolders under 04_Research_Experiments...")
    for s_name in sub_04:
        s_id = ensure_folder(s_name, registry["04_Research_Experiments"]["id"])
        registry["04_Research_Experiments"]["children"][s_name] = s_id

    # Subfolders of 06_Backups
    sub_06 = [
        "Source_Snapshots",
        "Model_Checkpoint_Snapshots",
        "Scientific_Data_Archives",
        "Recovery_Manifests",
    ]
    print("\nCreating subfolders under 06_Backups...")
    for s_name in sub_06:
        s_id = ensure_folder(s_name, registry["06_Backups"]["id"])
        registry["06_Backups"]["children"][s_name] = s_id

    # Save registry to reports/v3/drive_folder_registry.json
    reg_path = PROJECT_ROOT / "reports" / "v3" / "drive_folder_registry.json"
    reg_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"\n[OK] Folder hierarchy created. Registry saved to {reg_path}")

    # 3. Connection Test Upload & Verification
    print("\n[Step 3] Executing Connection Test Upload & Readback Verification...")
    test_src = PROJECT_ROOT / "reports" / "v3" / "VAYUMARG_DRIVE_CONNECTION_TEST.md"
    local_hash = compute_sha256(test_src)
    local_size = test_src.stat().st_size

    print(f"Uploading {test_src.name} ({local_size} bytes, SHA-256: {local_hash})...")
    up_res = run_gdrive(["mutate", "upload", str(test_src), "--parent", ROOT_FOLDER_ID])
    test_file_id = up_res.get("id") if isinstance(up_res, dict) else None
    assert test_file_id, "Upload returned no file ID!"
    print(f"Uploaded successfully. Remote File ID: {test_file_id}")

    # Readback download into temporary directory
    print("Performing readback verification...")
    with tempfile.TemporaryDirectory() as tmpdir:
        download_dest = Path(tmpdir) / "readback_test.md"
        run_gdrive(["readonly", "download", test_file_id, "--out", str(download_dest)])
        assert download_dest.exists(), "Download target missing!"
        download_hash = compute_sha256(download_dest)
        download_size = download_dest.stat().st_size
        
        print(f"Readback Size: {download_size} bytes (Expected: {local_size})")
        print(f"Readback Hash: {download_hash}")
        print(f"Local Hash:    {local_hash}")
        assert local_hash == download_hash, "Readback hash mismatch! Data corruption detected!"
        assert local_size == download_size, "Readback size mismatch!"
        print(">>> 100% BITWISE VERIFICATION CONFIRMED FOR CONNECTION TEST FILE <<<")

    # 4. Tier 1 Foundation Transfers
    print("\n[Step 4] Executing Tier 1 Foundation Document Transfers...")
    tier1_items = [
        {
            "local_path": PROJECT_ROOT / "reports" / "v3" / "P0_REPOSITORY_REALITY_AUDIT.md",
            "target_folder_id": registry["05_Project_Documentation"]["id"],
            "target_folder_name": "05_Project_Documentation",
        },
        {
            "local_path": PROJECT_ROOT / "reports" / "v3" / "P0_SCIENTIFIC_MODEL_BASELINE.md",
            "target_folder_id": registry["04_Research_Experiments"]["children"]["Evaluation_Ledgers"],
            "target_folder_name": "04_Research_Experiments/Evaluation_Ledgers",
        },
        {
            "local_path": PROJECT_ROOT / "reports" / "v3" / "P0_DATASET_PROVENANCE_AND_GAPS.md",
            "target_folder_id": registry["02_Scientific_Datasets"]["children"]["Dataset_Manifests"],
            "target_folder_name": "02_Scientific_Datasets/Dataset_Manifests",
        },
        {
            "local_path": PROJECT_ROOT / "data" / "processed" / "satellite" / "nasa_cyclone" / "dataset_manifest.json",
            "target_folder_id": registry["02_Scientific_Datasets"]["children"]["NASA_Tropical_Cyclone"],
            "target_folder_name": "02_Scientific_Datasets/NASA_Tropical_Cyclone",
        },
    ]

    transfer_ledger = [
        {
            "file_name": test_src.name,
            "local_rel_path": test_src.relative_to(PROJECT_ROOT).as_posix(),
            "drive_file_id": test_file_id,
            "parent_folder_id": ROOT_FOLDER_ID,
            "parent_folder_name": "Vayumarg (ROOT)",
            "size_bytes": local_size,
            "sha256": local_hash,
            "readback_verified": True,
            "status": "VERIFIED_SYNCHRONIZED",
        }
    ]

    for item in tier1_items:
        p = item["local_path"]
        f_hash = compute_sha256(p)
        f_size = p.stat().st_size
        print(f"\nUploading {p.name} ({f_size} bytes) -> {item['target_folder_name']}...")
        res = run_gdrive(["mutate", "upload", str(p), "--parent", item["target_folder_id"]])
        fid = res.get("id") if isinstance(res, dict) else None
        assert fid, f"Upload failed for {p.name}"
        
        # Verify readback
        with tempfile.TemporaryDirectory() as tmpdir:
            dl_path = Path(tmpdir) / p.name
            run_gdrive(["readonly", "download", fid, "--out", str(dl_path)])
            assert dl_path.exists(), "Downloaded file missing!"
            dl_hash = compute_sha256(dl_path)
            assert f_hash == dl_hash, f"Hash mismatch for {p.name}!"
            print(f"  [VERIFIED] Readback hash matches: {dl_hash[:16]}...")

        transfer_ledger.append({
            "file_name": p.name,
            "local_rel_path": p.relative_to(PROJECT_ROOT).as_posix(),
            "drive_file_id": fid,
            "parent_folder_id": item["target_folder_id"],
            "parent_folder_name": item["target_folder_name"],
            "size_bytes": f_size,
            "sha256": f_hash,
            "readback_verified": True,
            "status": "VERIFIED_SYNCHRONIZED",
        })

    # Save ledger
    ledger_path = PROJECT_ROOT / "reports" / "v3" / "transfer_ledger.json"
    ledger_path.write_text(json.dumps(transfer_ledger, indent=2), encoding="utf-8")
    print(f"\n[SUCCESS] Transfer ledger written to {ledger_path}")
    print("=" * 80)
    print("ALL INITIAL TRANSFERS COMPLETED AND 100% READBACK VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
