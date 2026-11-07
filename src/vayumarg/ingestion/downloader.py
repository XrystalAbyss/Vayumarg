"""Streamed, atomic HTTP downloader with cryptographic verification for IBTrACS datasets.

Adheres to scientific preservation principles:
1. Atomic writing via temporary `.part` files to prevent partial file corruption.
2. In-flight SHA-256 hash calculation and file size verification.
3. Exponential backoff retry strategy for resilient downloads.
4. Support for both curl (native Windows schannel TLS) and urllib backends.
5. Generation and persistent storage of cryptographic asset manifests.
"""

import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vayumarg.core.config import settings
from vayumarg.core.hashing import calculate_sha256, generate_manifest_record, save_manifest
from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.ingestion.downloader")

OFFICIAL_IBTRACS_NI_CSV_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs"
    "/v04r01/access/csv/ibtracs.NI.list.v04r01.csv"
)
DEFAULT_RAW_FILE_NAME = "ibtracs_ni_v04r01.csv"
DEFAULT_MANIFEST_FILE_NAME = "ibtracs_ni_v04r01_manifest.json"
KNOWN_NI_SHA256 = "6e0dd2dde1f22c4bf03995beb21944bf5976536c747b23ba85c6d300aeab69ff"
KNOWN_NI_SIZE_BYTES = 27895917


class DownloadError(Exception):
    """Raised when an asset download fails all retry attempts."""

    pass


class ChecksumMismatchError(DownloadError):
    """Raised when downloaded file does not match expected checksum."""

    pass


def _download_via_curl(url: str, part_path: Path, timeout_sec: float) -> None:
    """Download using system curl executable (optimal for Windows schannel TLS)."""
    curl_bin = shutil.which("curl") or shutil.which("curl.exe")
    if not curl_bin:
        raise FileNotFoundError("curl executable not available")

    cmd = [
        curl_bin,
        "-fSL",
        "--retry",
        "3",
        "--max-time",
        str(int(timeout_sec)),
        "-A",
        "Vayumarg/0.1 (Research Scientific System; VortexA-SIH2026)",
        "-o",
        str(part_path.resolve()),
        url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise DownloadError(f"curl download failed (exit code {res.returncode}): {res.stderr}")


def _download_via_urllib(url: str, part_path: Path, chunk_size: int, timeout_sec: float) -> None:
    """Download using Python standard library urllib."""
    headers = {
        "User-Agent": "Vayumarg/0.1 (Research Scientific System; VortexA-SIH2026)",
        "Accept": "text/csv, application/octet-stream, */*",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout_sec) as response:
        content_length = response.headers.get("Content-Length")
        remote_size = int(content_length) if content_length else None

        bytes_downloaded = 0
        with open(part_path, "wb") as f_out:
            while chunk := response.read(chunk_size):
                f_out.write(chunk)
                bytes_downloaded += len(chunk)

        if remote_size is not None and bytes_downloaded != remote_size:
            raise DownloadError(
                f"Incomplete download: received {bytes_downloaded} bytes, expected {remote_size}"
            )


def download_file(
    url: str,
    destination_path: Path | str,
    expected_sha256: str | None = None,
    expected_size_bytes: int | None = None,
    force_download: bool = False,
    chunk_size: int = 65536,
    max_retries: int = 4,
    initial_backoff_sec: float = 2.0,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """Download a file with streaming SHA-256 verification and atomic rename.

    Args:
        url: Remote HTTP/HTTPS URL.
        destination_path: Target local file path.
        expected_sha256: Optional known SHA-256 hash for integrity validation.
        expected_size_bytes: Optional expected content length in bytes.
        force_download: If True, redownload even if target exists and is valid.
        chunk_size: Streaming buffer size in bytes (default: 64 KB).
        max_retries: Number of connection retry attempts.
        initial_backoff_sec: Base seconds for exponential backoff.
        timeout_sec: Socket connection and read timeout.

    Returns:
        Manifest record containing file metadata, size, SHA-256, and timestamps.
    """
    dest = Path(destination_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest.with_name(f"{dest.name}.part")

    # If file exists and not forced, check validity
    if dest.is_file() and not force_download:
        existing_size = dest.stat().st_size
        existing_sha = calculate_sha256(dest)
        if expected_sha256 and existing_sha.lower() != expected_sha256.lower():
            logger.warning(
                "Existing file %s SHA-256 mismatch (%s != %s). Re-downloading.",
                dest,
                existing_sha,
                expected_sha256,
            )
        elif expected_size_bytes and existing_size != expected_size_bytes:
            logger.warning(
                "Existing file %s size mismatch (%d != %d). Re-downloading.",
                dest,
                existing_size,
                expected_size_bytes,
            )
        else:
            logger.info("Target file %s already exists and is verified. Skipping download.", dest)
            return generate_manifest_record(
                dest,
                asset_type="RAW_CSV",
                metadata={"source_url": url, "verified_at_utc": datetime.now(UTC).isoformat()},
            )

    last_exception: Exception | None = None
    use_curl = shutil.which("curl") is not None or shutil.which("curl.exe") is not None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Downloading %s (Attempt %d/%d) to %s", url, attempt, max_retries, part_path
            )
            if part_path.exists():
                part_path.unlink()

            if use_curl:
                try:
                    _download_via_curl(url, part_path, timeout_sec)
                except Exception as curl_err:
                    logger.warning("curl download failed: %s; falling back to urllib", curl_err)
                    _download_via_urllib(url, part_path, chunk_size, timeout_sec)
            else:
                _download_via_urllib(url, part_path, chunk_size, timeout_sec)

            # Verification of downloaded .part file
            actual_sha = calculate_sha256(part_path)
            actual_size = part_path.stat().st_size

            if expected_sha256 and actual_sha.lower() != expected_sha256.lower():
                part_path.unlink(missing_ok=True)
                raise ChecksumMismatchError(
                    f"Checksum mismatch for {url}: got {actual_sha}, expected {expected_sha256}"
                )

            if expected_size_bytes and actual_size != expected_size_bytes:
                part_path.unlink(missing_ok=True)
                raise DownloadError(
                    f"Size mismatch for {url}: got {actual_size} bytes, expected {expected_size_bytes}"
                )

            # Atomic rename from .part to destination
            if dest.exists():
                dest.unlink()
            part_path.rename(dest)

            logger.info(
                "Successfully downloaded and verified %s (%d bytes, SHA-256: %s)",
                dest.name,
                actual_size,
                actual_sha,
            )

            manifest_record = generate_manifest_record(
                dest,
                asset_type="RAW_CSV",
                metadata={
                    "source_url": url,
                    "download_time_utc": datetime.now(UTC).isoformat(),
                    "retries": attempt - 1,
                },
            )
            return manifest_record

        except (urllib.error.URLError, TimeoutError, OSError, DownloadError) as exc:
            last_exception = exc
            logger.warning(
                "Attempt %d/%d failed downloading %s: %s", attempt, max_retries, url, exc
            )
            if part_path.exists():
                part_path.unlink(missing_ok=True)

            if attempt < max_retries:
                backoff = initial_backoff_sec * (2 ** (attempt - 1))
                logger.info("Backing off for %.1f seconds before retry...", backoff)
                time.sleep(backoff)

    raise DownloadError(
        f"Failed to download {url} after {max_retries} attempts: {last_exception}"
    ) from last_exception


def download_official_ibtracs_ni(
    force: bool = False,
    destination_dir: Path | None = None,
    manifest_dir: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Download the official NOAA IBTrACS North Indian Ocean CSV and generate manifest.

    Args:
        force: If True, re-download even if already present and valid.
        destination_dir: Directory for raw file (defaults to data/raw).
        manifest_dir: Directory for manifest (defaults to data/manifests).

    Returns:
        Tuple of (local_file_path, manifest_dictionary).
    """
    raw_dir = destination_dir or settings.get_data_dir("raw")
    m_dir = manifest_dir or settings.MANIFEST_DIR
    m_dir.mkdir(parents=True, exist_ok=True)

    dest_file = raw_dir / DEFAULT_RAW_FILE_NAME
    manifest_file = m_dir / DEFAULT_MANIFEST_FILE_NAME

    manifest_record = download_file(
        url=OFFICIAL_IBTRACS_NI_CSV_URL,
        destination_path=dest_file,
        expected_sha256=KNOWN_NI_SHA256,
        expected_size_bytes=KNOWN_NI_SIZE_BYTES,
        force_download=force,
    )

    save_manifest(
        manifest_records=[manifest_record],
        output_path=manifest_file,
        manifest_name="ibtracs_ni_v04r01_raw",
    )
    logger.info("Saved raw dataset manifest to %s", manifest_file)

    return dest_file, manifest_record
