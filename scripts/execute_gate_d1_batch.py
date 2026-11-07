"""Sequential, fault-tolerant acquisition of Gate D1: TAUKTAE, FANI, and FENGAL."""

import hashlib
import os
import sys
import time
from pathlib import Path

import h5py
import requests

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.gate_d1_execution")

TOKEN_URL = "https://mosdac.gov.in/download_api/gettoken"
DOWNLOAD_URL = "https://mosdac.gov.in/download_api/download"
TARGET_DIR = Path("data/raw/satellite/insat_real")

CANDIDATES = [
    {
        "name": "TAUKTAE",
        "gid": "9293840",
        "filename": "3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5",
        "expected_size": 301621093,
    },
    {
        "name": "FANI",
        "gid": "7206464",
        "filename": "3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5",
        "expected_size": 303911822,
    },
    {
        "name": "FENGAL",
        "gid": "14687507",
        "filename": "3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5",
        "expected_size": 429759238,
    },
]

MAX_TOTAL_BUDGET_BYTES = 1100000000  # 1.1 GB ceiling to accommodate exact 1,035,292,153 bytes


def get_authenticated_token() -> str:
    username = os.getenv("MOSDAC_USERNAME") or "ishhangoyal"
    password = os.getenv("MOSDAC_PASSWORD") or "Ishhan@3004"
    resp = requests.post(TOKEN_URL, json={"username": username, "password": password}, timeout=15)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("No access token returned by MOSDAC.")
    return token


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_boundary(token: str, gid: str, part_file: Path) -> None:
    curr_len = part_file.stat().st_size
    check_len = min(1024, curr_len)
    start_offset = curr_len - check_len
    end_offset = curr_len - 1

    with open(part_file, "rb") as f:
        f.seek(start_offset)
        local_data = f.read(check_len)

    headers = {
        "Authorization": f"Bearer {token}",
        "Range": f"bytes={start_offset}-{end_offset}",
    }
    resp = requests.get(DOWNLOAD_URL, headers=headers, params={"id": gid}, timeout=15)
    resp.raise_for_status()
    if resp.status_code != 206:
        raise RuntimeError(f"Server did not return HTTP 206 for boundary check: {resp.status_code}")
    server_data = resp.content
    if local_data != server_data:
        raise ValueError(
            f"Boundary mismatch at offset {start_offset}-{end_offset}! Local != Server."
        )


def download_single_granule(
    cand: dict, token: str, total_transferred_so_far: int
) -> tuple[int, str, dict]:
    name = cand["name"]
    gid = cand["gid"]
    filename = cand["filename"]
    expected_size = cand["expected_size"]

    final_path = TARGET_DIR / filename
    part_path = TARGET_DIR / f"{filename}.part"

    if final_path.is_file() and final_path.stat().st_size == expected_size:
        print(f"\n[{name}] Final file already present and complete: {final_path.name}")
        with h5py.File(final_path, "r") as f:
            keys_count = len(f.keys())
        sha = compute_sha256(final_path)
        print(f"[{name}] SHA-256: {sha}")
        return (
            0,
            token,
            {
                "name": name,
                "status": "ALREADY_COMPLETE",
                "bytes_transferred": 0,
                "final_size": expected_size,
                "sha256": sha,
                "h5_keys": keys_count,
                "attempts": 0,
            },
        )

    bytes_downloaded_this_file = 0
    attempts = 0
    max_attempts = 30

    while attempts < max_attempts:
        attempts += 1
        current_size = part_path.stat().st_size if part_path.is_file() else 0

        if current_size >= expected_size:
            print(f"[{name}] Reached or exceeded expected size: {current_size}/{expected_size}")
            break

        print(
            f"\n[{name}] Attempt {attempts}/{max_attempts}: Resuming at {current_size:,} / {expected_size:,} bytes "
            f"({current_size / (1024 * 1024):.2f} MB / {expected_size / (1024 * 1024):.2f} MB, {current_size / expected_size * 100:.1f}%)"
        )
        sys.stdout.flush()

        if current_size > 0:
            try:
                verify_boundary(token, gid, part_path)
                print(f"[{name}] Boundary verification passed at offset {current_size:,}.")
            except Exception as e:
                print(f"[{name}] Boundary check failed ({e}). Refreshing token...")
                token = get_authenticated_token()
                verify_boundary(token, gid, part_path)
                print(f"[{name}] Boundary verification passed after token refresh.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Range": f"bytes={current_size}-",
        }
        params = {"id": gid}

        try:
            with requests.get(
                DOWNLOAD_URL, headers=headers, params=params, stream=True, timeout=25
            ) as r:
                if r.status_code == 401:
                    print(f"[{name}] HTTP 401 Unauthorized encountered. Refreshing token...")
                    token = get_authenticated_token()
                    time.sleep(2)
                    continue

                if r.status_code not in (200, 206):
                    print(
                        f"[{name}] Unexpected HTTP status: {r.status_code}. Response: {r.text[:200]}"
                    )
                    time.sleep(5)
                    continue

                mode = "ab" if current_size > 0 else "wb"
                chunk_counter = 0
                t_start = time.time()
                with open(part_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded_this_file += len(chunk)
                            total_transferred_so_far += len(chunk)
                            chunk_counter += 1

                            if total_transferred_so_far > MAX_TOTAL_BUDGET_BYTES:
                                raise RuntimeError(
                                    f"BUDGET CEILING EXCEEDED! Transferred {total_transferred_so_far} > {MAX_TOTAL_BUDGET_BYTES}."
                                )

                            if chunk_counter % 150 == 0:
                                sz = f.tell()
                                dt = time.time() - t_start
                                mb = sz / (1024 * 1024)
                                spd = (len(chunk) * 150) / (dt * 1024 * 1024) if dt > 0 else 0
                                print(
                                    f"  [{name}] {mb:.2f} MB / {expected_size / (1024 * 1024):.2f} MB ({sz / expected_size * 100:.1f}%) | ~{spd:.2f} MB/s",
                                    end="\r",
                                )
                                sys.stdout.flush()
                                t_start = time.time()

            print(f"\n[{name}] Stream loop ended normally for attempt {attempts}.")

        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as err:
            sz = part_path.stat().st_size if part_path.is_file() else 0
            print(
                f"\n[{name}] Interruption caught: {type(err).__name__}. Current size: {sz:,} bytes. Backing off 3s..."
            )
            time.sleep(3)
        except Exception as e:
            print(f"\n[{name}] Unexpected error: {e}. Backing off 5s...")
            time.sleep(5)

    final_size = part_path.stat().st_size if part_path.is_file() else 0
    if final_size != expected_size:
        raise RuntimeError(
            f"[{name}] Download finished with size {final_size} bytes, but expected {expected_size} bytes!"
        )

    print(f"\n[{name}] Validating HDF5 structural integrity...")
    with h5py.File(part_path, "r") as h5:
        root_keys = list(h5.keys())
        print(f"[{name}] Successfully read HDF5 container. Found {len(root_keys)} root keys.")
        for required_ds in ["IMG_TIR1", "IMG_WV", "IMG_TIR2", "IMG_MIR", "Latitude", "Longitude"]:
            if required_ds not in h5:
                raise ValueError(f"Required dataset {required_ds} missing from {name} HDF5!")

    print(f"[{name}] Computing SHA-256 checksum...")
    sha = compute_sha256(part_path)
    print(f"[{name}] SHA-256: {sha}")

    # Atomic promotion
    if final_path.is_file():
        final_path.unlink()
    part_path.rename(final_path)
    print(f"[{name}] Atomically promoted to: {final_path.name}")

    meta = {
        "name": name,
        "gid": gid,
        "filename": filename,
        "status": "COMPLETED_VERIFIED",
        "bytes_transferred": bytes_downloaded_this_file,
        "final_size": expected_size,
        "sha256": sha,
        "h5_keys": len(root_keys),
        "attempts": attempts,
    }
    return bytes_downloaded_this_file, token, meta


def main():
    print("=" * 80)
    print("VAYUMARG MILESTONE F2.4 — GATE D1 BATCH EXECUTION")
    print("=" * 80)
    print(f"Budget Limit: {MAX_TOTAL_BUDGET_BYTES:,} bytes (~1.035 GB target)")
    print(f"Target Directory: {TARGET_DIR.resolve()}")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    token = get_authenticated_token()
    print("Authentication successful with MOSDAC.")

    total_bytes = 0
    results = []

    for cand in CANDIDATES:
        b_trans, token, meta = download_single_granule(cand, token, total_bytes)
        total_bytes += b_trans
        results.append(meta)
        print(
            f"\nFinished {cand['name']}. Total batch bytes transferred so far: {total_bytes:,} bytes."
        )

    print("\n" + "=" * 80)
    print("GATE D1 BATCH ACQUISITION SUMMARY")
    print("=" * 80)
    print(
        f"Total New Bytes Transferred: {total_bytes:,} bytes ({total_bytes / (1024 * 1024):.2f} MB)"
    )
    for res in results:
        print(
            f"  {res['name']} (gId {res['gid']}): {res['status']} | Size: {res['final_size']:,} bytes | SHA: {res['sha256']} | Keys: {res['h5_keys']} | Attempts: {res['attempts']}"
        )


if __name__ == "__main__":
    main()
