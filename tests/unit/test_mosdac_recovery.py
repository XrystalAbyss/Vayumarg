"""Unit tests for fault-tolerant MOSDAC recovery and acquisition module (Milestone F2.4)."""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import h5py
import pytest
import requests

from vayumarg.satellite.mosdac_recovery import (
    FaultTolerantMOSDACDownloader,
    NetworkFailureClass,
    PartialDownloadMetadata,
    classify_request_exception,
    probe_range_capability,
)


class MockRawStream:
    """Mock raw stream for requests response."""

    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self.stream.read(n)


def create_minimal_hdf5_bytes() -> bytes:
    """Generate minimal valid in-memory HDF5 byte array."""
    bio = io.BytesIO()
    with h5py.File(bio, "w") as f:
        f.create_dataset("test_channel", data=[1, 2, 3, 4])
    return bio.getvalue()


# --- 1. Range Capability Probe Tests ---


def test_probe_range_capability_supported_206():
    """Verify probe returns supported=True when server returns HTTP 206 with valid Content-Range."""
    payload = b"X" * 1024
    mock_resp = MagicMock()
    mock_resp.status_code = 206
    mock_resp.headers = {
        "Content-Range": "bytes 0-1023/50000000",
        "Content-Length": "1024",
        "ETag": '"test-etag-123"',
        "Last-Modified": "Wed, 21 Oct 2024 07:28:00 GMT",
    }
    mock_resp.raw = MockRawStream(payload)
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.get", return_value=mock_resp):
        res = probe_range_capability("dummy_token", "14514765")
        assert res.supported is True
        assert res.status_code == 206
        assert res.total_size == 50000000
        assert res.error_class is None
        assert res.etag == '"test-etag-123"'


def test_probe_range_capability_unsupported_200():
    """Verify probe aborts and flags unsupported when server returns HTTP 200 to Range request."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "Content-Length": "50000000",
        "ETag": '"test-etag-200"',
    }
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.get", return_value=mock_resp):
        res = probe_range_capability("dummy_token", "14514765")
        assert res.supported is False
        assert res.status_code == 200
        assert res.error_class == NetworkFailureClass.RANGE_NOT_SUPPORTED
        assert res.total_size == 50000000


def test_probe_range_capability_missing_content_range():
    """Verify probe detects malformed 206 response lacking Content-Range header."""
    mock_resp = MagicMock()
    mock_resp.status_code = 206
    mock_resp.headers = {"Content-Length": "1024"}
    mock_resp.raw = MockRawStream(b"X" * 1024)
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.get", return_value=mock_resp):
        res = probe_range_capability("dummy_token", "14514765")
        assert res.supported is False
        assert res.error_class == NetworkFailureClass.RANGE_METADATA_MISMATCH


def test_probe_range_capability_auth_failure_401():
    """Verify probe classifies HTTP 401 as auth failure."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {}
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.get", return_value=mock_resp):
        res = probe_range_capability("invalid_token", "14514765")
        assert res.supported is False
        assert res.status_code == 401
        assert res.error_class == NetworkFailureClass.HTTP_401_AUTH_FAILURE


def test_probe_range_capability_rate_limit_429():
    """Verify probe classifies HTTP 429 as rate limit."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.get", return_value=mock_resp):
        res = probe_range_capability("dummy_token", "14514765")
        assert res.supported is False
        assert res.error_class == NetworkFailureClass.HTTP_429_RATE_LIMITED


def test_probe_range_capability_server_error_503():
    """Verify probe classifies HTTP 503 as server error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.headers = {}
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.get", return_value=mock_resp):
        res = probe_range_capability("dummy_token", "14514765")
        assert res.supported is False
        assert res.error_class == NetworkFailureClass.HTTP_5XX_SERVER_FAILURE


# --- 2. Exception Classification Tests ---


def test_classify_request_exception():
    """Verify structured failure mapping for various socket/network exceptions."""
    assert (
        classify_request_exception(requests.exceptions.ConnectTimeout())
        == NetworkFailureClass.CONNECTION_TIMEOUT
    )
    assert (
        classify_request_exception(requests.exceptions.ReadTimeout())
        == NetworkFailureClass.READ_TIMEOUT
    )
    assert (
        classify_request_exception(requests.exceptions.SSLError())
        == NetworkFailureClass.HTTP_5XX_SERVER_FAILURE
    )
    assert (
        classify_request_exception(
            requests.exceptions.ConnectionError(
                "Failed to establish a new connection: [Errno 11001] getaddrinfo failed"
            )
        )
        == NetworkFailureClass.DNS_RESOLUTION_FAILURE
    )
    assert (
        classify_request_exception(requests.exceptions.ConnectionError("Connection reset by peer"))
        == NetworkFailureClass.SERVER_STREAM_INTERRUPTED
    )


# --- 3. Partial Metadata Sidecar Tests ---


def test_partial_metadata_sidecar_roundtrip(tmp_path: Path):
    """Verify sidecar serialization and deserialization."""
    sidecar_path = tmp_path / "test.h5.part.meta.json"
    meta = PartialDownloadMetadata(
        granule_gid="14514765",
        dataset_id="3SIMG_L1B_STD",
        expected_filename="test.h5",
        total_size_bytes=288673840,
        bytes_downloaded=141557760,
        etag='"etag123"',
        last_modified="Fri, 25 Oct 2024 23:30:00 GMT",
        range_supported=True,
        created_at_utc=1730490000.0,
        last_updated_at_utc=1730490500.0,
    )
    meta.save(sidecar_path)
    assert sidecar_path.is_file()

    loaded = PartialDownloadMetadata.load(sidecar_path)
    assert loaded is not None
    assert loaded.granule_gid == "14514765"
    assert loaded.bytes_downloaded == 141557760
    assert loaded.range_supported is True


# --- 4. Fault-Tolerant Downloader Unit Tests ---


def test_downloader_atomic_promotion_and_completion(tmp_path: Path):
    """Verify downloader completes transfer, verifies HDF5, and atomically promotes file."""
    h5_bytes = create_minimal_hdf5_bytes()
    total_len = len(h5_bytes)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Length": str(total_len)}
    mock_resp.iter_content.return_value = [h5_bytes[:50], h5_bytes[50:]]
    mock_resp.__enter__.return_value = mock_resp

    downloader = FaultTolerantMOSDACDownloader(output_dir=tmp_path)
    with patch("requests.get", return_value=mock_resp):
        out_path, prog = downloader.download_granule(
            bearer_token="dummy",
            granule_gid="12345",
            expected_filename="test_granule.h5",
            dataset_id="TEST_PROD",
            known_range_support=False,
        )

    assert out_path.is_file()
    assert out_path.name == "test_granule.h5"
    assert not (tmp_path / "test_granule.h5.tmp").exists()
    assert not (tmp_path / "test_granule.h5.part").exists()
    assert prog.failure_class == NetworkFailureClass.SUCCESS
    assert prog.total_bytes == total_len

    # Verify HDF5 is readable
    with h5py.File(out_path, "r") as f:
        assert "test_channel" in f


def test_downloader_resumable_transfer(tmp_path: Path):
    """Verify downloader resumes from existing byte offset when range_supported=True."""
    h5_bytes = create_minimal_hdf5_bytes()
    split_point = len(h5_bytes) // 2

    # Write initial .part file and sidecar
    part_file = tmp_path / "resumable.h5.part"
    part_file.write_bytes(h5_bytes[:split_point])
    sidecar = tmp_path / "resumable.h5.part.meta.json"
    meta = PartialDownloadMetadata(
        granule_gid="999",
        dataset_id="TEST",
        expected_filename="resumable.h5",
        total_size_bytes=len(h5_bytes),
        bytes_downloaded=split_point,
        etag=None,
        last_modified=None,
        range_supported=True,
        created_at_utc=0,
        last_updated_at_utc=0,
    )
    meta.save(sidecar)

    mock_resp = MagicMock()
    mock_resp.status_code = 206
    mock_resp.headers = {
        "Content-Range": f"bytes {split_point}-{len(h5_bytes) - 1}/{len(h5_bytes)}",
        "Content-Length": str(len(h5_bytes) - split_point),
    }
    mock_resp.iter_content.return_value = [h5_bytes[split_point:]]
    mock_resp.__enter__.return_value = mock_resp

    downloader = FaultTolerantMOSDACDownloader(output_dir=tmp_path)
    with patch("requests.get", return_value=mock_resp):
        out_path, prog = downloader.download_granule(
            bearer_token="dummy",
            granule_gid="999",
            expected_filename="resumable.h5",
            dataset_id="TEST",
            known_range_support=True,
        )

    assert out_path.is_file()
    assert out_path.stat().st_size == len(h5_bytes)
    assert not part_file.exists()
    assert not sidecar.exists()
    assert prog.resumed_from_byte == split_point


def test_downloader_corrupt_hdf5_rejection(tmp_path: Path):
    """Verify downloader rejects corrupt HDF5 and retries."""
    corrupt_bytes = b"CORRUPT_NOT_HDF5_DATA" * 50

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Length": str(len(corrupt_bytes))}
    mock_resp.iter_content.return_value = [corrupt_bytes]
    mock_resp.__enter__.return_value = mock_resp

    downloader = FaultTolerantMOSDACDownloader(output_dir=tmp_path)
    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(ConnectionError, match="Failed to acquire granule"):
            downloader.download_granule(
                bearer_token="dummy",
                granule_gid="bad_hdf",
                expected_filename="corrupt.h5",
                dataset_id="TEST",
                known_range_support=False,
                max_retries=2,
                backoff_seconds=0.01,
            )

    # Destination should not exist
    assert not (tmp_path / "corrupt.h5").exists()
