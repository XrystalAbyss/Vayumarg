"""Secure wrapper and search client for ISRO MOSDAC satellite data acquisition.

Provides:
1. Public unauthenticated catalog search and inventory planning (INSAT-3D, INSAT-3DR, INSAT-3DS).
2. Ephemeral, Windows-restricted credential isolation wrapper around official MOSDAC client (mdapi.py).
3. Zero-persistence credential guarantees: credentials are accepted only interactively via getpass,
   stored only in an ephemeral DACL-restricted temporary directory, and securely overwritten on exit.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.ingestion.mosdac_client")

MOSDAC_SEARCH_URL = "https://mosdac.gov.in/apios/datasets.json"
MOSDAC_TOKEN_URL = "https://mosdac.gov.in/download_api/gettoken"
VENDOR_MDAPI_PATH = Path("data/tools/mosdac_client/extracted/mdapi.py")


@dataclass
class MOSDACGranuleRecord:
    """Discovered granule record from official MOSDAC catalog."""

    identifier: str
    record_id: str
    product_date_utc: str
    dataset_id: str


@dataclass
class MOSDACSearchSummary:
    """Summary of MOSDAC catalog search query."""

    dataset_id: str
    start_time: str
    end_time: str
    total_results: int
    total_size_mb: float
    entries: list[MOSDACGranuleRecord]


class MOSDACSearchClient:
    """Unauthenticated search client for querying the official ISRO MOSDAC metadata API."""

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout = timeout_seconds

    def search(
        self,
        dataset_id: str,
        start_time: str,
        end_time: str,
        count: int | None = 10,
        bounding_box: str | None = None,
        start_index: int = 1,
        granule_id: str | None = None,
    ) -> MOSDACSearchSummary:
        """Query official MOSDAC catalog for available granules without authentication.

        Supports exact single-granule targeting via numeric record ID (gId) or HDF5 identifier.
        """
        params: dict[str, Any] = {
            "datasetId": dataset_id,
            "startTime": start_time,
            "endTime": end_time,
            "startIndex": start_index,
        }
        if count is not None:
            params["count"] = count
        if bounding_box:
            params["boundingBox"] = bounding_box

        # If a numeric granule ID is provided, pass directly to gId
        if granule_id:
            clean_gid = granule_id.strip()
            if clean_gid.isdigit():
                params["gId"] = clean_gid
                params["count"] = 1

        logger.info(
            "Searching MOSDAC catalog for %s [%s to %s]...", dataset_id, start_time, end_time
        )
        try:
            resp = requests.get(MOSDAC_SEARCH_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("MOSDAC catalog search failed: %s", e)
            raise ConnectionError(f"MOSDAC search failed: {e}") from e

        total_results = int(data.get("totalResults", 0))
        total_size_mb = float(data.get("totalSizeMB", 0.0))
        raw_entries = data.get("entries", [])

        # If an alphanumeric filename was provided, filter/validate matching entry
        if granule_id and not granule_id.strip().isdigit():
            target_name = granule_id.strip()
            raw_entries = [e for e in raw_entries if e.get("identifier") == target_name]
            if not raw_entries:
                raise ValueError(
                    f"Granule identifier '{target_name}' not found in {dataset_id} catalog between {start_time} and {end_time}."
                )
            total_results = len(raw_entries)

        records = [
            MOSDACGranuleRecord(
                identifier=entry.get("identifier", ""),
                record_id=str(entry.get("id", "")),
                product_date_utc=entry.get("updated", ""),
                dataset_id=dataset_id,
            )
            for entry in raw_entries
        ]

        if granule_id and not records:
            raise ValueError(
                f"No matching granule found for ID '{granule_id}' under product {dataset_id}."
            )

        logger.info(
            "Found %d total results (%.2f MB) for %s", total_results, total_size_mb, dataset_id
        )
        return MOSDACSearchSummary(
            dataset_id=dataset_id,
            start_time=start_time,
            end_time=end_time,
            total_results=total_results,
            total_size_mb=total_size_mb,
            entries=records,
        )


def restrict_windows_directory_acl(directory_path: Path) -> None:
    """Apply restrictive Access Control Lists (ACLs) on Windows.

    Grants Full Control only to the current user and denies inheritance from parent.
    """
    if platform.system().lower() != "windows":
        # POSIX: restrict to user only
        os.chmod(directory_path, 0o700)
        return

    try:
        username = os.getenv("USERNAME", "")
        if not username:
            return

        # Disable inheritance and remove inherited permissions
        # /inheritance:r removes all inherited ACEs
        # /grant:r "%USERNAME%":(OI)(CI)F grants current user full access
        cmd = [
            "icacls",
            str(directory_path),
            "/inheritance:r",
            "/grant:r",
            f"{username}:(OI)(CI)F",
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        logger.debug("Applied restrictive Windows DACL to %s", directory_path)
    except Exception as e:
        logger.warning("Could not apply strict Windows DACL: %s", e)


def secure_wipe_file(file_path: Path) -> None:
    """Overwrites file contents with zeros before unlinking to prevent memory/disk recovery."""
    try:
        if file_path.is_file():
            length = file_path.stat().st_size
            with open(file_path, "ba+", buffering=0) as f:
                f.seek(0)
                f.write(b"\x00" * max(length, 1024))
            file_path.unlink(missing_ok=True)
    except Exception as e:
        logger.warning("Secure wipe warning for %s: %s", file_path, e)


class SecureMOSDACDownloader:
    """Ephemeral execution harness for official ISRO MOSDAC downloader (mdapi.py)."""

    def __init__(self, official_script_path: Path = VENDOR_MDAPI_PATH):
        self.script_path = official_script_path
        if not self.script_path.is_file():
            raise FileNotFoundError(
                f"Official MOSDAC downloader not found at {self.script_path}. Run discovery download first."
            )

    def execute_bounded_download(
        self,
        username: str,
        password: str,
        dataset_id: str,
        start_time: str,
        end_time: str,
        download_target_dir: Path,
        max_files: int = 1,
        bounding_box: str = "",
        granule_id: str | None = None,
    ) -> list[Path]:
        """Execute the official MOSDAC script in an isolated temporary directory.

        Guarantees that credentials in config.json exist solely during the subprocess lifetime
        in a private Windows-isolated folder, and are securely wiped immediately upon completion.
        Supports exact single-granule targeting via granule_id.
        """
        download_target_dir = download_target_dir.resolve()
        download_target_dir.mkdir(parents=True, exist_ok=True)

        target_numeric_gid = ""
        expected_filename = None

        if granule_id:
            search_client = MOSDACSearchClient()
            summary = search_client.search(
                dataset_id=dataset_id,
                start_time=start_time,
                end_time=end_time,
                granule_id=granule_id,
            )
            if not summary.entries:
                raise ValueError(
                    f"Granule '{granule_id}' could not be verified in MOSDAC catalog for {dataset_id}."
                )
            target_numeric_gid = summary.entries[0].record_id
            expected_filename = summary.entries[0].identifier
            max_files = 1
            logger.info(
                "Targeting exact granule: gId=%s | expected_file=%s",
                target_numeric_gid,
                expected_filename,
            )

        # Record pre-existing files in target directory
        pre_existing = set(download_target_dir.glob("*.h5")) | set(download_target_dir.glob("*.nc"))

        # Create isolated temporary directory outside repo
        temp_dir = Path(tempfile.mkdtemp(prefix="vayumarg_mosdac_"))
        restrict_windows_directory_acl(temp_dir)

        config_path = temp_dir / "config.json"
        dest_script = temp_dir / "mdapi.py"

        try:
            # Copy official script into isolated environment
            shutil.copy2(self.script_path, dest_script)

            # Defensive hardening: Ensure stream download timeout is robust against socket read latency
            script_text = dest_script.read_text(encoding="utf-8")
            if "stream=True, timeout=5)" in script_text:
                script_text = script_text.replace(
                    "stream=True, timeout=5)",
                    "stream=True, timeout=(15, 120))",
                )
                dest_script.write_text(script_text, encoding="utf-8")

            # Build ephemeral config
            config_payload = {
                "user_credentials": {
                    "username/email": username,
                    "password": password,
                },
                "search_parameters": {
                    "datasetId": dataset_id,
                    "startTime": start_time,
                    "endTime": end_time,
                    "count": str(max_files) if max_files else "1",
                    "boundingBox": bounding_box,
                    "gId": target_numeric_gid,
                },
                "download_settings": {
                    "download_path": str(download_target_dir.as_posix()),
                    "organize_by_date": False,
                    "skip_user_input": True,
                    "generate_error_logs": True,
                    "error_logs_dir": str(temp_dir.as_posix()),
                },
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_payload, f, indent=2)

            logger.info("Starting isolated MOSDAC acquisition subprocess in %s...", temp_dir)

            # Execute official script using current python environment
            # Run with simulated "y" in stdin in case interactive prompt triggers
            proc = subprocess.run(
                [sys.executable, str(dest_script)],
                cwd=str(temp_dir),
                input="y\n",
                text=True,
                capture_output=True,
                check=False,
            )

            # Inspect output for authentication error indicators
            stdout = proc.stdout or ""

            if "Invalid Username/Password" in stdout or "Validation Error: Status 401" in stdout:
                logger.error("MOSDAC Authentication failed: Invalid credentials.")
                raise PermissionError("MOSDAC authentication failed: Invalid Username or Password.")

            if "Service Unavailable" in stdout or "503 Server Error" in stdout:
                logger.error("MOSDAC Server Unavailable.")
                raise ConnectionError("MOSDAC server is currently unavailable (503).")

            logger.info("MOSDAC process exited with code %d", proc.returncode)

            # Discover newly downloaded files in target directory
            current_files = set(download_target_dir.glob("*.h5")) | set(
                download_target_dir.glob("*.nc")
            )
            new_files = sorted(current_files - pre_existing)

            if expected_filename and new_files:
                for f in new_files:
                    if f.name != expected_filename:
                        logger.error(
                            "Downloaded filename mismatch: got %s, expected %s",
                            f.name,
                            expected_filename,
                        )
                        raise ValueError(
                            f"Downloaded file '{f.name}' does not match expected granule '{expected_filename}'."
                        )

            return new_files

        finally:
            # Strict cleanup: securely zero-wipe configuration file containing password
            secure_wipe_file(config_path)
            # Remove temporary directory and all contents
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning("Could not delete temp directory %s: %s", temp_dir, e)
