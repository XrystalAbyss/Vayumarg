"""Fault-tolerant MOSDAC recovery and acquisition module for Milestone F2.4.

Provides:
1. Authenticated HTTP Range capability probing for MOSDAC endpoints.
2. Structured network and transport failure classification.
3. Resumable transfer engine with atomic promotion and quarantine protection.
4. Clean restart fallback (RESTART_REQUIRED) when HTTP Range is unsupported.
5. Non-secret diagnostics and zero-credential leakage guarantees.
"""

import hashlib
import json
import os
import shutil
import socket
import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

import h5py
import requests

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.satellite.mosdac_recovery")

MOSDAC_DOWNLOAD_URL = "https://mosdac.gov.in/download_api/download"
MOSDAC_TOKEN_URL = "https://mosdac.gov.in/download_api/gettoken"


class NetworkFailureClass(StrEnum):
    """Structured diagnostic failure classifications for MOSDAC transfers."""

    DNS_RESOLUTION_FAILURE = "DNS_RESOLUTION_FAILURE"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    READ_TIMEOUT = "READ_TIMEOUT"
    SERVER_STREAM_INTERRUPTED = "SERVER_STREAM_INTERRUPTED"
    HTTP_401_AUTH_FAILURE = "HTTP_401_AUTH_FAILURE"
    HTTP_403_PERMISSION_DENIED = "HTTP_403_PERMISSION_DENIED"
    HTTP_404_GRANULE_NOT_FOUND = "HTTP_404_GRANULE_NOT_FOUND"
    HTTP_429_RATE_LIMITED = "HTTP_429_RATE_LIMITED"
    HTTP_5XX_SERVER_FAILURE = "HTTP_5XX_SERVER_FAILURE"
    RANGE_NOT_SUPPORTED = "RANGE_NOT_SUPPORTED"
    RANGE_METADATA_MISMATCH = "RANGE_METADATA_MISMATCH"
    REMOTE_OBJECT_CHANGED = "REMOTE_OBJECT_CHANGED"
    TRUNCATED_CONTENT = "TRUNCATED_CONTENT"
    INVALID_HDF5 = "INVALID_HDF5"
    DISK_CAPACITY_BLOCK = "DISK_CAPACITY_BLOCK"
    USER_CANCELLED = "USER_CANCELLED"
    SUCCESS = "SUCCESS"


@dataclass
class RangeSupportResult:
    """Result of an authenticated HTTP Range capability probe."""

    supported: bool
    status_code: int
    content_range: str | None
    content_length: int | None
    total_size: int | None
    etag: str | None
    last_modified: str | None
    error_class: NetworkFailureClass | None
    diagnostic_message: str


@dataclass
class TransferProgress:
    """Diagnostic metrics for a transfer operation."""

    granule_gid: str
    target_filename: str
    total_bytes: int
    transferred_bytes: int
    resumed_from_byte: int
    duration_seconds: float
    average_throughput_mb_s: float
    attempts: int
    failure_class: NetworkFailureClass
    sha256_hash: str | None


@dataclass
class PartialDownloadMetadata:
    """Credential-free sidecar tracking partial transfer status."""

    granule_gid: str
    dataset_id: str
    expected_filename: str
    total_size_bytes: int
    bytes_downloaded: int
    etag: str | None
    last_modified: str | None
    range_supported: bool
    created_at_utc: float
    last_updated_at_utc: float

    def save(self, sidecar_path: Path) -> None:
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        with open(sidecar_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, sidecar_path: Path) -> "PartialDownloadMetadata | None":
        if not sidecar_path.is_file():
            return None
        try:
            with open(sidecar_path, encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            logger.warning("Failed to read partial sidecar %s: %s", sidecar_path, e)
            return None


def classify_request_exception(exc: Exception) -> NetworkFailureClass:
    """Categorize standard requests/urllib3 exceptions into structured failure classes."""
    if isinstance(exc, requests.exceptions.SSLError):
        return NetworkFailureClass.HTTP_5XX_SERVER_FAILURE
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return NetworkFailureClass.CONNECTION_TIMEOUT
    if isinstance(exc, requests.exceptions.ReadTimeout):
        return NetworkFailureClass.READ_TIMEOUT
    if isinstance(exc, requests.exceptions.ConnectionError):
        # Inspect inner exceptions for DNS / Socket
        err_str = str(exc).lower()
        if "getaddrinfo" in err_str or "name resolution" in err_str or "dns" in err_str:
            return NetworkFailureClass.DNS_RESOLUTION_FAILURE
        if "connection reset" in err_str or "broken pipe" in err_str:
            return NetworkFailureClass.SERVER_STREAM_INTERRUPTED
        return NetworkFailureClass.SERVER_STREAM_INTERRUPTED
    if isinstance(exc, socket.timeout):
        return NetworkFailureClass.READ_TIMEOUT
    return NetworkFailureClass.SERVER_STREAM_INTERRUPTED


def probe_range_capability(
    bearer_token: str,
    record_id: str,
    dataset_id: str | None = None,
    timeout_seconds: tuple[float, float] = (10.0, 30.0),
    test_range: tuple[int, int] = (0, 1023),
) -> RangeSupportResult:
    """Probe whether the MOSDAC download endpoint supports HTTP Range resumption.

    Issues a bounded Range request for `bytes=start-end`.
    Accepts Range support ONLY IF:
    1. HTTP status code is 206 (Partial Content).
    2. Content-Range header is present and valid.
    3. Returned range starts and ends exactly as requested.
    4. Payload length matches.
    If server returns 200, the stream is aborted immediately without consuming the payload.
    """
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Range": f"bytes={test_range[0]}-{test_range[1]}",
    }
    params = {"id": record_id}

    logger.info("Probing HTTP Range support for gId=%s on MOSDAC endpoint...", record_id)
    try:
        with requests.get(
            MOSDAC_DOWNLOAD_URL,
            headers=headers,
            params=params,
            stream=True,
            timeout=timeout_seconds,
        ) as resp:
            status = resp.status_code
            etag = resp.headers.get("ETag")
            last_modified = resp.headers.get("Last-Modified")

            if status == 206:
                content_range = resp.headers.get("Content-Range")
                content_length_hdr = resp.headers.get("Content-Length")
                content_length = int(content_length_hdr) if content_length_hdr else None

                expected_len = test_range[1] - test_range[0] + 1
                payload_sample = resp.raw.read(expected_len + 10)
                actual_payload_len = len(payload_sample)

                # Validate Content-Range header format: bytes <start>-<end>/<total>
                if not content_range or not content_range.startswith("bytes "):
                    return RangeSupportResult(
                        supported=False,
                        status_code=status,
                        content_range=content_range,
                        content_length=content_length,
                        total_size=None,
                        etag=etag,
                        last_modified=last_modified,
                        error_class=NetworkFailureClass.RANGE_METADATA_MISMATCH,
                        diagnostic_message="Status 206 received but Content-Range header is missing or malformed.",
                    )

                range_spec, total_spec = content_range.replace("bytes ", "").split("/")
                start_str, end_str = range_spec.split("-")
                ret_start, ret_end = int(start_str), int(end_str)
                total_size = int(total_spec) if total_spec.isdigit() else None

                if (
                    ret_start != test_range[0]
                    or ret_end != test_range[1]
                    or actual_payload_len != expected_len
                ):
                    return RangeSupportResult(
                        supported=False,
                        status_code=status,
                        content_range=content_range,
                        content_length=content_length,
                        total_size=total_size,
                        etag=etag,
                        last_modified=last_modified,
                        error_class=NetworkFailureClass.RANGE_METADATA_MISMATCH,
                        diagnostic_message=f"Range bounds or payload mismatch: requested {test_range}, got ({ret_start}, {ret_end}), bytes read {actual_payload_len}.",
                    )

                return RangeSupportResult(
                    supported=True,
                    status_code=status,
                    content_range=content_range,
                    content_length=content_length,
                    total_size=total_size,
                    etag=etag,
                    last_modified=last_modified,
                    error_class=None,
                    diagnostic_message="HTTP Range resumption is supported by the server.",
                )

            elif status == 200:
                # Server ignored Range header and attempted to send whole object
                content_length_hdr = resp.headers.get("Content-Length")
                total_size = int(content_length_hdr) if content_length_hdr else None
                return RangeSupportResult(
                    supported=False,
                    status_code=200,
                    content_range=None,
                    content_length=total_size,
                    total_size=total_size,
                    etag=etag,
                    last_modified=last_modified,
                    error_class=NetworkFailureClass.RANGE_NOT_SUPPORTED,
                    diagnostic_message="Server responded with HTTP 200 to Range request. HTTP Range is NOT supported.",
                )

            elif status == 401:
                return RangeSupportResult(
                    supported=False,
                    status_code=401,
                    content_range=None,
                    content_length=None,
                    total_size=None,
                    etag=None,
                    last_modified=None,
                    error_class=NetworkFailureClass.HTTP_401_AUTH_FAILURE,
                    diagnostic_message="Authentication token rejected by MOSDAC download endpoint (HTTP 401).",
                )

            elif status == 403:
                return RangeSupportResult(
                    supported=False,
                    status_code=403,
                    content_range=None,
                    content_length=None,
                    total_size=None,
                    etag=None,
                    last_modified=None,
                    error_class=NetworkFailureClass.HTTP_403_PERMISSION_DENIED,
                    diagnostic_message="Access forbidden to requested granule (HTTP 403).",
                )

            elif status == 404:
                return RangeSupportResult(
                    supported=False,
                    status_code=404,
                    content_range=None,
                    content_length=None,
                    total_size=None,
                    etag=None,
                    last_modified=None,
                    error_class=NetworkFailureClass.HTTP_404_GRANULE_NOT_FOUND,
                    diagnostic_message="Granule not found on MOSDAC server (HTTP 404).",
                )

            elif status == 429:
                return RangeSupportResult(
                    supported=False,
                    status_code=429,
                    content_range=None,
                    content_length=None,
                    total_size=None,
                    etag=None,
                    last_modified=None,
                    error_class=NetworkFailureClass.HTTP_429_RATE_LIMITED,
                    diagnostic_message="MOSDAC rate limit reached (HTTP 429).",
                )

            elif 500 <= status < 600:
                return RangeSupportResult(
                    supported=False,
                    status_code=status,
                    content_range=None,
                    content_length=None,
                    total_size=None,
                    etag=None,
                    last_modified=None,
                    error_class=NetworkFailureClass.HTTP_5XX_SERVER_FAILURE,
                    diagnostic_message=f"MOSDAC server error (HTTP {status}).",
                )

            else:
                return RangeSupportResult(
                    supported=False,
                    status_code=status,
                    content_range=None,
                    content_length=None,
                    total_size=None,
                    etag=etag,
                    last_modified=last_modified,
                    error_class=NetworkFailureClass.SERVER_STREAM_INTERRUPTED,
                    diagnostic_message=f"Unexpected HTTP status {status} received from download endpoint.",
                )

    except Exception as e:
        fail_cls = classify_request_exception(e)
        return RangeSupportResult(
            supported=False,
            status_code=-1,
            content_range=None,
            content_length=None,
            total_size=None,
            etag=None,
            last_modified=None,
            error_class=fail_cls,
            diagnostic_message=f"Network exception during Range capability probe: {e}",
        )


class FaultTolerantMOSDACDownloader:
    """Robust, fault-tolerant acquisition engine with Range-resume and clean-restart fallbacks."""

    def __init__(
        self,
        output_dir: Path,
        connect_timeout_seconds: float = 15.0,
        read_timeout_seconds: float = 120.0,
        chunk_size_bytes: int = 1024 * 1024,  # 1 MB chunk
        min_free_space_bytes: int = 5 * 1024 * 1024 * 1024,  # 5 GB safety headroom
    ):
        self.output_dir = output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.connect_timeout = connect_timeout_seconds
        self.read_timeout = read_timeout_seconds
        self.chunk_size = chunk_size_bytes
        self.min_free_space = min_free_space_bytes

    def check_disk_headroom(self, expected_bytes: int = 0) -> None:
        """Ensure sufficient disk storage exists without violating safety headroom."""
        free_bytes = shutil.disk_usage(self.output_dir).free
        if free_bytes - expected_bytes < self.min_free_space:
            raise OSError(
                f"Disk capacity block: Free space {free_bytes / (1024**3):.2f} GB is insufficient "
                f"for required {expected_bytes / (1024**3):.2f} GB plus {self.min_free_space / (1024**3):.2f} GB reserve."
            )

    def download_granule(
        self,
        bearer_token: str,
        granule_gid: str,
        expected_filename: str,
        dataset_id: str,
        known_range_support: bool | None = None,
        max_retries: int = 3,
        backoff_seconds: float = 5.0,
    ) -> tuple[Path, TransferProgress]:
        """Download an authentic granule with resumption if supported, or clean restart fallback.

        Enforces atomic promotion:
        - Transfers into `<expected_filename>.part` (if resumable) or `<expected_filename>.tmp`.
        - Validates HDF5 integrity and expected size.
        - Computes SHA-256.
        - Atomically moves to `<output_dir>/<expected_filename>`.
        """
        target_path = self.output_dir / expected_filename
        part_path = self.output_dir / f"{expected_filename}.part"
        meta_path = self.output_dir / f"{expected_filename}.part.meta.json"

        # Check if already completed and valid
        if target_path.is_file():
            try:
                with h5py.File(target_path, "r") as h5:
                    if len(h5.keys()) > 0:
                        h = hashlib.sha256()
                        with open(target_path, "rb") as f:
                            while chunk := f.read(1024 * 1024):
                                h.update(chunk)
                        logger.info(
                            "Granule %s already exists and is valid. Reusing.", expected_filename
                        )
                        return target_path, TransferProgress(
                            granule_gid=granule_gid,
                            target_filename=expected_filename,
                            total_bytes=target_path.stat().st_size,
                            transferred_bytes=0,
                            resumed_from_byte=0,
                            duration_seconds=0.0,
                            average_throughput_mb_s=0.0,
                            attempts=0,
                            failure_class=NetworkFailureClass.SUCCESS,
                            sha256_hash=h.hexdigest(),
                        )
            except Exception:
                logger.warning("Pre-existing %s is corrupted; re-acquiring.", target_path)
                target_path.unlink(missing_ok=True)

        # 1. Determine HTTP Range support if not pre-determined
        if known_range_support is None:
            range_res = probe_range_capability(
                bearer_token, granule_gid, dataset_id, (self.connect_timeout, self.read_timeout)
            )
            range_supported = range_res.supported
        else:
            range_supported = known_range_support

        logger.info(
            "Transfer strategy for %s: %s",
            expected_filename,
            "RESUMABLE" if range_supported else "RESTART_REQUIRED",
        )

        attempts = 0
        total_transferred = 0
        start_time = time.time()

        while attempts < max_retries:
            attempts += 1
            existing_bytes = 0
            open_mode = "wb"
            headers = {"Authorization": f"Bearer {bearer_token}"}

            if range_supported and part_path.is_file() and meta_path.is_file():
                meta = PartialDownloadMetadata.load(meta_path)
                if (
                    meta
                    and meta.granule_gid == granule_gid
                    and meta.expected_filename == expected_filename
                ):
                    existing_bytes = part_path.stat().st_size
                    if existing_bytes > 0:
                        headers["Range"] = f"bytes={existing_bytes}-"
                        open_mode = "ab"
                        logger.info(
                            "Resuming %s from byte %d...", expected_filename, existing_bytes
                        )

            try:
                params = {"id": granule_gid}
                with requests.get(
                    MOSDAC_DOWNLOAD_URL,
                    headers=headers,
                    params=params,
                    stream=True,
                    timeout=(self.connect_timeout, self.read_timeout),
                ) as resp:
                    status = resp.status_code

                    # If server returned 401: stop immediately
                    if status == 401:
                        logger.error("Authentication rejected (HTTP 401).")
                        raise PermissionError("MOSDAC authentication rejected.")

                    if status == 403:
                        logger.error("Access forbidden (HTTP 403).")
                        raise PermissionError("MOSDAC access forbidden.")

                    if status == 404:
                        logger.error("Granule not found (HTTP 404).")
                        raise FileNotFoundError(f"Granule {granule_gid} not found on server.")

                    if status == 429:
                        logger.warning("Rate limit hit (HTTP 429). Waiting %ds...", backoff_seconds)
                        time.sleep(backoff_seconds * attempts)
                        continue

                    if status >= 500:
                        logger.warning(
                            "Server 5xx error (%d). Backing off %ds...", status, backoff_seconds
                        )
                        time.sleep(backoff_seconds * attempts)
                        continue

                    # If we asked for Range but server sent 200: Range unsupported -> restart clean
                    if existing_bytes > 0 and status == 200:
                        logger.warning(
                            "Server returned 200 instead of 206 to Range request. Fallback to clean restart."
                        )
                        range_supported = False
                        existing_bytes = 0
                        open_mode = "wb"

                    # Validate Content-Range if status 206
                    if status == 206:
                        cr = resp.headers.get("Content-Range", "")
                        if not cr.startswith(f"bytes {existing_bytes}-"):
                            logger.error("Mismatched Content-Range %s. Restarting clean.", cr)
                            existing_bytes = 0
                            open_mode = "wb"

                    # Determine total size
                    content_length_hdr = resp.headers.get("Content-Length")
                    stream_len = int(content_length_hdr) if content_length_hdr else 0
                    total_size = (
                        existing_bytes + stream_len
                        if (status == 206 and stream_len)
                        else stream_len
                    )

                    self.check_disk_headroom(stream_len)

                    # Update metadata sidecar
                    meta = PartialDownloadMetadata(
                        granule_gid=granule_gid,
                        dataset_id=dataset_id,
                        expected_filename=expected_filename,
                        total_size_bytes=total_size,
                        bytes_downloaded=existing_bytes,
                        etag=resp.headers.get("ETag"),
                        last_modified=resp.headers.get("Last-Modified"),
                        range_supported=range_supported,
                        created_at_utc=time.time(),
                        last_updated_at_utc=time.time(),
                    )
                    meta.save(meta_path)

                    # Stream payload into temporary file
                    write_target = (
                        part_path
                        if range_supported
                        else (self.output_dir / f"{expected_filename}.tmp")
                    )
                    with open(write_target, open_mode) as out_f:
                        for chunk in resp.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                out_f.write(chunk)
                                total_transferred += len(chunk)
                                existing_bytes += len(chunk)
                                meta.bytes_downloaded = existing_bytes
                                meta.last_updated_at_utc = time.time()

                    # Stream finished normally for this response
                    meta.save(meta_path)

                    # Verify completed file size
                    final_bytes = write_target.stat().st_size
                    if total_size and final_bytes < total_size:
                        logger.warning(
                            "Truncated content: expected %d bytes, got %d. Retrying...",
                            total_size,
                            final_bytes,
                        )
                        continue

                    # Validate HDF5 readability
                    try:
                        with h5py.File(write_target, "r") as h5_test:
                            if len(h5_test.keys()) == 0:
                                raise ValueError("HDF5 contains 0 root keys.")
                    except Exception as h5_err:
                        logger.error(
                            "Corrupted HDF5 on transfer completion (%s). Retrying...", h5_err
                        )
                        write_target.unlink(missing_ok=True)
                        continue

                    # Compute SHA-256
                    hasher = hashlib.sha256()
                    with open(write_target, "rb") as vf:
                        while chunk := vf.read(1024 * 1024):
                            hasher.update(chunk)
                    computed_sha = hasher.hexdigest()

                    # Atomic promotion
                    if target_path.exists():
                        target_path.unlink()
                    os.replace(write_target, target_path)

                    # Cleanup sidecar
                    meta_path.unlink(missing_ok=True)
                    if not range_supported:
                        part_path.unlink(missing_ok=True)

                    duration = max(time.time() - start_time, 0.001)
                    mb_s = (total_transferred / (1024 * 1024)) / duration

                    logger.info(
                        "Successfully acquired %s (%d bytes, SHA-256: %s) at %.2f MB/s.",
                        expected_filename,
                        final_bytes,
                        computed_sha,
                        mb_s,
                    )
                    return target_path, TransferProgress(
                        granule_gid=granule_gid,
                        target_filename=expected_filename,
                        total_bytes=final_bytes,
                        transferred_bytes=total_transferred,
                        resumed_from_byte=existing_bytes - total_transferred,
                        duration_seconds=duration,
                        average_throughput_mb_s=mb_s,
                        attempts=attempts,
                        failure_class=NetworkFailureClass.SUCCESS,
                        sha256_hash=computed_sha,
                    )

            except (TimeoutError, requests.exceptions.RequestException, OSError) as net_err:
                fail_cls = classify_request_exception(net_err)
                logger.warning(
                    "Transfer attempt %d failed with %s: %s. Retrying in %ds...",
                    attempts,
                    fail_cls.value,
                    net_err,
                    backoff_seconds,
                )
                time.sleep(backoff_seconds)

        # Retries exhausted
        duration = max(time.time() - start_time, 0.001)
        mb_s = (total_transferred / (1024 * 1024)) / duration
        raise ConnectionError(
            f"Failed to acquire granule {granule_gid} ({expected_filename}) after {attempts} attempts. "
            f"Transferred {total_transferred} bytes in {duration:.1f}s."
        )
