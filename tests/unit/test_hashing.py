"""Unit tests for SHA-256 cryptographic hashing and manifest creation."""

import pytest

from vayumarg.core.hashing import (
    calculate_bytes_sha256,
    calculate_sha256,
    generate_manifest_record,
    save_manifest,
)


@pytest.mark.unit
def test_bytes_sha256():
    """Verify SHA-256 computation on known byte sequence."""
    data = b"Vayumarg Scientific Foundation"
    # hashlib.sha256(b"Vayumarg Scientific Foundation").hexdigest()
    expected = "5b967673d77c6fc7d8c310062f9950064da4e7e8704d0670227e59bb1c970b3e"
    assert calculate_bytes_sha256(data) == expected


@pytest.mark.unit
def test_file_sha256(tmp_path):
    """Verify SHA-256 checksumming on a physical file."""
    test_file = tmp_path / "sample_track.csv"
    test_file.write_bytes(b"timestamp,lat,lon,wind\n2024-05-18T00:00:00Z,12.5,88.2,45\n")

    checksum = calculate_sha256(test_file)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)


@pytest.mark.unit
def test_generate_and_save_manifest(tmp_path):
    """Verify end-to-end manifest generation and persistence."""
    sample_file = tmp_path / "insat3d_synthetic.nc"
    sample_file.write_bytes(b"SYNTHETIC_NETCDF_PAYLOAD_FOR_TESTING")

    record = generate_manifest_record(
        sample_file, asset_type="SATELLITE_NETCDF", metadata={"sensor": "IMAGER"}
    )
    assert record["file_name"] == "insat3d_synthetic.nc"
    assert record["asset_type"] == "SATELLITE_NETCDF"
    assert record["size_bytes"] == len(b"SYNTHETIC_NETCDF_PAYLOAD_FOR_TESTING")

    manifest_file = tmp_path / "manifest.json"
    saved_path = save_manifest([record], manifest_file, manifest_name="raw_satellite_v1")
    assert saved_path.exists()
