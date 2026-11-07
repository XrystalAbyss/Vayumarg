"""Batch acquisition driver for Milestone F2.3 authentic MOSDAC satellite granules."""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vayumarg.core.logging import get_logger
from vayumarg.ingestion.mosdac_client import SecureMOSDACDownloader

logger = get_logger("vayumarg.acquire_f2_3_batch")

MANIFEST_PATH = Path("reports/F2_3_ACQUISITION_MANIFEST.json")
OUTPUT_DIR = Path("data/raw/satellite/insat_real")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    username = os.getenv("MOSDAC_USERNAME") or "ishhangoyal"
    password = os.getenv("MOSDAC_PASSWORD") or "Ishhan@3004"

    if not username or not password:
        logger.error("MOSDAC credentials are missing.")
        sys.exit(1)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    downloader = SecureMOSDACDownloader()

    results = []

    for item in manifest["granules"]:
        idx = item["index"]
        storm = item["storm_name"]
        ds_id = item["dataset_id"]
        gid = item["granule_gid"]
        expected_name = item["expected_identifier"]
        s_date = item["product_date_utc"][:10]
        target_file = OUTPUT_DIR / expected_name

        print(f"\n[{idx}/6] Processing {storm} ({expected_name})...")

        if target_file.is_file() and target_file.stat().st_size > 100 * 1024 * 1024:
            print(
                f" -> File already exists ({target_file.stat().st_size / (1024 * 1024):.2f} MB). Verifying SHA-256..."
            )
            sha = compute_sha256(target_file)
            print(f" -> Verified existing: {sha}")
            results.append(
                {
                    "index": idx,
                    "storm": storm,
                    "gid": gid,
                    "filename": expected_name,
                    "size_bytes": target_file.stat().st_size,
                    "sha256": sha,
                    "status": "ALREADY_PRESENT_VERIFIED",
                }
            )
            continue

        print(f" -> Initiating authenticated download for gId={gid}...")
        t0 = time.time()
        try:
            acquired = downloader.execute_bounded_download(
                username=username,
                password=password,
                dataset_id=ds_id,
                start_time=s_date,
                end_time=s_date,
                download_target_dir=OUTPUT_DIR,
                max_files=1,
                granule_id=gid,
            )
            elapsed = time.time() - t0
            if not acquired:
                print(f" -> ERROR: No files acquired for {expected_name}!")
                results.append(
                    {
                        "index": idx,
                        "storm": storm,
                        "gid": gid,
                        "filename": expected_name,
                        "status": "FAILED_NO_OUTPUT",
                    }
                )
                continue

            saved_file = acquired[0]
            sha = compute_sha256(saved_file)
            size = saved_file.stat().st_size
            print(
                f" -> SUCCESS in {elapsed:.1f}s: {saved_file.name} ({size / (1024 * 1024):.2f} MB)"
            )
            print(f"    SHA-256: {sha}")
            results.append(
                {
                    "index": idx,
                    "storm": storm,
                    "gid": gid,
                    "filename": saved_file.name,
                    "size_bytes": size,
                    "sha256": sha,
                    "download_time_s": round(elapsed, 1),
                    "status": "ACQUIRED_AND_VERIFIED",
                }
            )
        except Exception as e:
            print(f" -> EXCEPTION during acquisition of {expected_name}: {e}")
            results.append(
                {
                    "index": idx,
                    "storm": storm,
                    "gid": gid,
                    "filename": expected_name,
                    "error": str(e),
                    "status": "FAILED",
                }
            )

    out_summary = Path("reports/F2_3_BATCH_ACQUISITION_RESULTS.json")
    with open(out_summary, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAcquisition run finished. Summary written to {out_summary}")


if __name__ == "__main__":
    main()
