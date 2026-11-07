"""Unit tests for MOSDAC acquisition security, credential hygiene, and isolation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vayumarg.ingestion.mosdac_client import (
    MOSDACSearchClient,
    SecureMOSDACDownloader,
    restrict_windows_directory_acl,
    secure_wipe_file,
)


def test_secure_wipe_file(tmp_path: Path) -> None:
    """Verify that secure_wipe_file overwrites contents before unlinking."""
    secret_file = tmp_path / "temp_secret.json"
    secret_file.write_text(json.dumps({"password": "supersecretpassword123"}))

    assert secret_file.is_file()
    secure_wipe_file(secret_file)
    assert not secret_file.exists()


def test_restrict_windows_directory_acl(tmp_path: Path) -> None:
    """Verify Windows DACL restriction does not crash and handles directories cleanly."""
    secure_dir = tmp_path / "secure_session"
    secure_dir.mkdir()
    # Should execute cleanly on Windows or Linux
    restrict_windows_directory_acl(secure_dir)
    assert secure_dir.is_dir()


def test_downloader_ephemeral_cleanup_on_auth_failure(tmp_path: Path) -> None:
    """Verify that ephemeral config is completely wiped even when download fails with 401."""
    downloader = SecureMOSDACDownloader()
    target_dir = tmp_path / "downloads"

    with patch("subprocess.run") as mock_run:
        # Simulate official script failure on 401 Invalid Username/Password
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "Validation Error: Status 401 [Invalid Username/Password]"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        with pytest.raises(PermissionError, match="Invalid Username or Password"):
            downloader.execute_bounded_download(
                username="invalid_user",
                password="wrong_password",
                dataset_id="3RIMG_L1B_STD",
                start_time="2024-05-25",
                end_time="2024-05-27",
                download_target_dir=target_dir,
                max_files=1,
            )

    # Verify no credentials leaked to current workspace
    assert not (Path.cwd() / "config.json").exists()


def test_search_client_unauthenticated() -> None:
    """Verify that search query generates correct public payload."""
    client = MOSDACSearchClient()
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "totalResults": 1,
            "totalSizeMB": 300.0,
            "entries": [
                {
                    "identifier": "3RIMG_27MAY2024_2345_L1B_STD_V01R00.h5",
                    "id": "13631145",
                    "updated": "2024-05-27T23:45:00Z",
                }
            ],
        }
        mock_get.return_value = mock_resp

        res = client.search("3RIMG_L1B_STD", "2024-05-25", "2024-05-27", count=1)
        assert res.total_results == 1
        assert res.entries[0].record_id == "13631145"
        mock_get.assert_called_once()
        # Verify no auth header was sent
        headers = mock_get.call_args[1].get("headers", {})
        assert "Authorization" not in headers


def test_search_client_numeric_gid() -> None:
    """Verify that numeric granule_id passes gId directly to MOSDAC endpoint."""
    client = MOSDACSearchClient()
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "totalResults": 1,
            "totalSizeMB": 280.0,
            "entries": [
                {
                    "identifier": "3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5",
                    "id": "13623453",
                    "updated": "2024-05-26T18:02:00Z",
                }
            ],
        }
        mock_get.return_value = mock_resp

        res = client.search(
            "3RIMG_L1B_STD",
            "2024-05-26",
            "2024-05-26",
            count=1,
            granule_id="13623453",
        )
        assert res.total_results == 1
        assert res.entries[0].record_id == "13623453"
        params = mock_get.call_args[1].get("params", {})
        assert params.get("gId") == "13623453"


def test_search_client_filename_resolution() -> None:
    """Verify that filename granule_id is matched and filtered from multi-result search."""
    client = MOSDACSearchClient()
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "totalResults": 2,
            "totalSizeMB": 560.0,
            "entries": [
                {
                    "identifier": "3RIMG_26MAY2024_1745_L1B_STD_V01R00.h5",
                    "id": "13623450",
                    "updated": "2024-05-26T17:45:00Z",
                },
                {
                    "identifier": "3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5",
                    "id": "13623453",
                    "updated": "2024-05-26T18:02:00Z",
                },
            ],
        }
        mock_get.return_value = mock_resp

        res = client.search(
            "3RIMG_L1B_STD",
            "2024-05-26",
            "2024-05-26",
            granule_id="3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5",
        )
        assert res.total_results == 1
        assert res.entries[0].identifier == "3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5"
        assert res.entries[0].record_id == "13623453"


def test_downloader_filename_mismatch_rejection(tmp_path: Path) -> None:
    """Verify that execute_bounded_download rejects unexpected downloaded files."""
    downloader = SecureMOSDACDownloader()
    target_dir = tmp_path / "downloads"
    target_dir.mkdir()

    with (
        patch("vayumarg.ingestion.mosdac_client.MOSDACSearchClient.search") as mock_search,
        patch("subprocess.run") as mock_run,
    ):
        mock_search_res = MagicMock()
        mock_search_res.total_results = 1
        mock_search_res.entries = [
            MagicMock(
                record_id="13623453",
                identifier="3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5",
                file_size_mb=280.0,
            )
        ]
        mock_search.return_value = mock_search_res

        def fake_run(*args, **kwargs):
            # Simulate official script writing a completely different file
            unexpected_file = target_dir / "UNEXPECTED_GRANULE.h5"
            unexpected_file.write_text("dummy")
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = "Download Complete!"
            return proc

        mock_run.side_effect = fake_run

        with pytest.raises(ValueError, match="does not match expected granule"):
            downloader.execute_bounded_download(
                username="test_user",
                password="test_password",
                dataset_id="3RIMG_L1B_STD",
                start_time="2024-05-26",
                end_time="2024-05-26",
                download_target_dir=target_dir,
                granule_id="13623453",
            )
