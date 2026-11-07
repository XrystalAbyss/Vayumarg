"""Vayumarg 3.0 — Phase F Isolated Restoration Smoke Test."""

import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

SOURCE_FILE = Path(r"C:\Users\astra\Desktop\Project\Vayumarg\reports\v3\P0_REPOSITORY_REALITY_AUDIT.md")
FILE_ID = "1iLBrCLqEuGObMGbycU78tgAw-XI74DcC"
EXPECTED_NAME = "P0_REPOSITORY_REALITY_AUDIT.md"
EXPECTED_SIZE = 11484
EXPECTED_SHA256 = "e4c066552a08854537b5b82d6d8095f4c066f85c0b18fb5789b059a5343c50ea"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    print("=" * 80)
    print("PHASE F: ISOLATED RESTORATION SMOKE TEST")
    print(f"Target Remote File ID: {FILE_ID}")
    print(f"Source Reference: {SOURCE_FILE}")
    print("=" * 80)

    # 1. Capture mtime and hash of original local file prior to test
    orig_mtime_before = SOURCE_FILE.stat().st_mtime
    orig_size_before = SOURCE_FILE.stat().st_size
    orig_hash_before = compute_sha256(SOURCE_FILE)
    assert orig_size_before == EXPECTED_SIZE, "Source size unexpected!"
    assert orig_hash_before == EXPECTED_SHA256, "Source hash unexpected!"
    print(f"[PRE-CHECK] Local source file intact (mtime: {orig_mtime_before}, size: {orig_size_before})")

    # 2. Perform timed download into an isolated temporary directory
    with tempfile.TemporaryDirectory(prefix="vayumarg_restore_test_") as tmpdir:
        dest_path = Path(tmpdir) / EXPECTED_NAME
        print(f"[RESTORING] Downloading {FILE_ID} to isolated temp dir: {dest_path}...")
        
        t0 = time.perf_counter()
        cmd = ["cmd.exe", "/c", "gdrive", "readonly", "download", FILE_ID, "--out", str(dest_path)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        elapsed_sec = time.perf_counter() - t0
        
        print(f"[RESTORED] Download completed in {elapsed_sec:.3f} seconds.")
        print(f"  CLI stdout: {res.stdout.strip()}")
        
        # 3. Assertions on restored file
        assert dest_path.exists(), "Restored file missing!"
        restored_size = dest_path.stat().st_size
        restored_hash = compute_sha256(dest_path)
        
        print(f"  Restored Filename: {dest_path.name} (Expected: {EXPECTED_NAME})")
        print(f"  Restored Size:     {restored_size} bytes (Expected: {EXPECTED_SIZE})")
        print(f"  Restored SHA-256:  {restored_hash}")
        print(f"  Expected SHA-256:  {EXPECTED_SHA256}")
        
        assert dest_path.name == EXPECTED_NAME, "Filename mismatch!"
        assert restored_size == EXPECTED_SIZE, "Size mismatch!"
        assert restored_hash == EXPECTED_SHA256, "Cryptographic hash mismatch!"
        print(">>> RESULT: 100% BITWISE EQUALITY CONFIRMED FOR RESTORED ARTIFACT <<<")

    # 4. Verify original source was never touched or overwritten
    orig_mtime_after = SOURCE_FILE.stat().st_mtime
    orig_size_after = SOURCE_FILE.stat().st_size
    orig_hash_after = compute_sha256(SOURCE_FILE)
    assert orig_mtime_before == orig_mtime_after, "Local file mtime changed!"
    assert orig_size_before == orig_size_after, "Local file size changed!"
    assert orig_hash_before == orig_hash_after, "Local file content changed!"
    print(f"[POST-CHECK] Zero local file mutation verified (Local source remains untouched).")

    # 5. Output smoke test report summary
    smoke_record = {
        "test_target": EXPECTED_NAME,
        "drive_file_id": FILE_ID,
        "restored_size_bytes": restored_size,
        "expected_size_bytes": EXPECTED_SIZE,
        "restored_sha256": restored_hash,
        "expected_sha256": EXPECTED_SHA256,
        "elapsed_seconds": round(elapsed_sec, 3),
        "transfer_rate_kb_s": round((restored_size / 1024) / max(elapsed_sec, 0.001), 2),
        "bitwise_match": True,
        "local_source_untouched": True,
        "verdict": "VERIFIED_BYTE_FOR_BYTE",
    }
    print("\nSmoke Test Record:")
    print(json.dumps(smoke_record, indent=2))

if __name__ == "__main__":
    main()

