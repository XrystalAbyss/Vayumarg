"""Cryptographic hashing and dataset manifest generation.

Provides stable SHA-256 checksumming for raw source assets, interim arrays,
and processed training/validation manifests.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def calculate_sha256(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Calculate the hexadecimal SHA-256 hash of a file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Target file does not exist: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def calculate_bytes_sha256(data: bytes) -> str:
    """Calculate the hexadecimal SHA-256 hash of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def generate_manifest_record(
    file_path: Path | str,
    asset_type: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an immutable asset manifest record for scientific tracking."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for manifest generation: {path}")

    file_stat = path.stat()
    sha256_hash = calculate_sha256(path)

    return {
        "file_name": path.name,
        "relative_path": str(path.as_posix()),
        "asset_type": asset_type,
        "size_bytes": file_stat.st_size,
        "sha256": sha256_hash,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "metadata": metadata or {},
    }


def save_manifest(
    manifest_records: list[dict[str, Any]],
    output_path: Path | str,
    manifest_name: str,
) -> Path:
    """Save an immutable manifest file with its own cryptographic hash."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "manifest_name": manifest_name,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "record_count": len(manifest_records),
        "records": manifest_records,
    }

    manifest_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    manifest_hash = calculate_bytes_sha256(manifest_bytes)
    payload["manifest_sha256"] = manifest_hash

    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return out
