"""Script to execute Gate B: Authenticated single-granule recovery for Cyclone DANA (gId 14514765) with robust multi-attempt resume loop."""

import hashlib
import os
import sys
import time
from pathlib import Path

import h5py
import requests

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.gate_b_recovery")

TARGET_GID = "14514765"
DATASET_ID = "3SIMG_L1B_STD"
FILENAME = "3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5"
EXPECTED_TOTAL_SIZE = 275275100
PART_PATH = Path("data/raw/satellite/insat_real") / f"{FILENAME}.part"
FINAL_PATH = Path("data/raw/satellite/insat_real") / FILENAME
SIDECAR_PATH = Path("data/raw/satellite/insat_real") / f"{FILENAME}.part.meta.json"
TOKEN_URL = "https://mosdac.gov.in/download_api/gettoken"
DOWNLOAD_URL = "https://mosdac.gov.in/download_api/download"


def get_authenticated_token() -> str:
    username = os.getenv("MOSDAC_USERNAME") or "ishhangoyal"
    password = os.getenv("MOSDAC_PASSWORD") or "Ishhan@3004"
    if not username or not password:
        raise ValueError("Missing MOSDAC credentials.")

    payload = {"username": username, "password": password}
    resp = requests.post(TOKEN_URL, json=payload, timeout=15)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("No access token returned.")
    return token


def verify_boundary_offset(token: str, part_file: Path) -> None:
    """Verify that the last 1024 bytes of the local .part file match the server exactly at that offset."""
    curr_len = part_file.stat().st_size
    check_len = min(1024, curr_len)
    start_offset = curr_len - check_len
    end_offset = curr_len - 1

    with open(part_file, "rb") as f:
        f.seek(start_offset)
        local_boundary = f.read(check_len)

    headers = {
        "Authorization": f"Bearer {token}",
        "Range": f"bytes={start_offset}-{end_offset}",
    }
    params = {"id": TARGET_GID}
    resp = requests.get(DOWNLOAD_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    if resp.status_code != 206:
        raise ValueError(f"Expected 206 for boundary probe, got {resp.status_code}")

    server_boundary = resp.content
    if local_boundary != server_boundary:
        raise ValueError(
            f"Boundary mismatch at offset {start_offset}-{end_offset}! Retained file does not match server stream."
        )

    logger.info(
        "Retained file boundary verification PASSED at offset %d-%d.", start_offset, end_offset
    )


def execute_recovery(max_attempts: int = 25):
    if not PART_PATH.is_file():
        raise FileNotFoundError(f"Part file missing: {PART_PATH}")

    total_start_time = time.time()
    total_resumed_bytes = 0
    attempt = 0
    token = get_authenticated_token()

    while attempt < max_attempts:
        attempt += 1
        current_size = PART_PATH.stat().st_size
        logger.info(
            "--- Attempt %d/%d: Current size %d / %d bytes (%.2f%%) ---",
            attempt,
            max_attempts,
            current_size,
            EXPECTED_TOTAL_SIZE,
            (current_size / EXPECTED_TOTAL_SIZE) * 100,
        )

        if current_size >= EXPECTED_TOTAL_SIZE:
            logger.info("All bytes have already been transferred.")
            break

        # 1. Boundary verification
        try:
            verify_boundary_offset(token, PART_PATH)
        except Exception as e:
            logger.warning("Boundary check failed (%s). Refreshing token and retrying...", e)
            try:
                token = get_authenticated_token()
                verify_boundary_offset(token, PART_PATH)
            except Exception as e2:
                logger.error("Persistent boundary error: %s", e2)
                raise

        # 2. Issue Resume Request
        resume_range_header = f"bytes={current_size}-"
        headers = {
            "Authorization": f"Bearer {token}",
            "Range": resume_range_header,
        }
        params = {"id": TARGET_GID}

        logger.info("Requesting resume range: %s...", resume_range_header)
        attempt_start = time.time()
        try:
            with requests.get(
                DOWNLOAD_URL, headers=headers, params=params, stream=True, timeout=(15, 60)
            ) as resp:
                if resp.status_code == 401:
                    logger.warning("Token expired (401). Refreshing token...")
                    token = get_authenticated_token()
                    continue

                if resp.status_code != 206:
                    logger.error("Server returned non-206 status: %d", resp.status_code)
                    raise ValueError(
                        f"Server rejected range request with status {resp.status_code}"
                    )

                content_range = resp.headers.get("Content-Range", "")
                logger.info("Server Content-Range: %s", content_range)
                expected_cr_prefix = (
                    f"bytes {current_size}-{EXPECTED_TOTAL_SIZE - 1}/{EXPECTED_TOTAL_SIZE}"
                )
                if content_range != expected_cr_prefix:
                    logger.error(
                        "Content-Range mismatch! Expected '%s', got '%s'",
                        expected_cr_prefix,
                        content_range,
                    )
                    raise ValueError(f"Content-Range mismatch: {content_range}")

                # Stream into part file
                chunk_size = 512 * 1024  # 512 KB
                bytes_this_attempt = 0
                with open(PART_PATH, "ab") as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                            bytes_this_attempt += len(chunk)
                            total_resumed_bytes += len(chunk)

                logger.info(
                    "Attempt %d stream finished cleanly: +%d bytes.",
                    attempt,
                    bytes_this_attempt,
                )

        except (requests.exceptions.RequestException, Exception) as stream_err:
            elapsed_attempt = max(time.time() - attempt_start, 0.001)
            new_size = PART_PATH.stat().st_size
            net_gain = new_size - current_size
            logger.warning(
                "Attempt %d interrupted after %.1fs (+%d bytes transferred, now %d bytes): %s. Backing off 3s before resume...",
                attempt,
                elapsed_attempt,
                net_gain,
                new_size,
                stream_err,
            )
            time.sleep(3.0)

    final_size = PART_PATH.stat().st_size
    duration = max(time.time() - total_start_time, 0.001)
    avg_speed = (total_resumed_bytes / (1024 * 1024)) / duration

    if final_size != EXPECTED_TOTAL_SIZE:
        raise ValueError(
            f"Final file size mismatch after {attempt} attempts! Expected {EXPECTED_TOTAL_SIZE}, got {final_size}"
        )

    # 4. HDF5 Validation
    logger.info("Validating HDF5 integrity on completed file...")
    with h5py.File(PART_PATH, "r") as h5:
        keys = list(h5.keys())
        logger.info("HDF5 root keys: %d keys found -> %s", len(keys), keys[:10])
        if len(keys) == 0:
            raise ValueError("HDF5 has 0 keys!")

    # 5. Compute SHA-256
    logger.info("Computing SHA-256 checksum...")
    hasher = hashlib.sha256()
    with open(PART_PATH, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    sha256_hash = hasher.hexdigest()
    logger.info("Final completed SHA-256: %s", sha256_hash)

    # 6. Atomic promotion
    if FINAL_PATH.exists():
        FINAL_PATH.unlink()
    os.replace(PART_PATH, FINAL_PATH)
    SIDECAR_PATH.unlink(missing_ok=True)
    logger.info("Atomically promoted %s to %s", PART_PATH.name, FINAL_PATH.name)

    return {
        "granule_gid": TARGET_GID,
        "filename": FILENAME,
        "path": str(FINAL_PATH),
        "total_bytes": final_size,
        "total_bytes_resumed": total_resumed_bytes,
        "attempts": attempt,
        "duration_seconds": duration,
        "average_mb_s": avg_speed,
        "sha256": sha256_hash,
    }


if __name__ == "__main__":
    try:
        res = execute_recovery()
        print("\n=== GATE B RECOVERY SUCCESSFUL ===")
        for k, v in res.items():
            print(f"  {k}: {v}")
    except Exception as e:
        logger.exception("Gate B recovery failed: %s", e)
        sys.exit(1)
