"""Unit and reconciliation tests for Milestone F2.3R: asset audit, partial download gating, and database identity."""

import json
from pathlib import Path

import h5py
import pytest

from vayumarg.core.config import Settings

RECONCILIATION_JSON_PATH = Path("reports/F2_3R_GRANULE_RECONCILIATION.json")
RAW_DIR = Path("data/raw/satellite/insat_real")
AUTHENTIC_REMAL_HDF5 = RAW_DIR / "3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5"
EXPECTED_REMAL_SHA = "5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807"


def test_database_identity_configuration() -> None:
    """Verify that configuration defines canonical 'vayumarg' and 'vayumarg_test' databases, not 'vayumarg_dev'."""
    settings = Settings()
    assert settings.POSTGRES_DB == "vayumarg"
    assert settings.POSTGRES_TEST_DB == "vayumarg_test"
    assert not settings.DATABASE_URL.endswith("/vayumarg_dev")
    assert not settings.TEST_DATABASE_URL.endswith("/vayumarg_dev")
    assert settings.DATABASE_URL.endswith("/vayumarg")
    assert settings.TEST_DATABASE_URL.endswith("/vayumarg_test")


def test_authentic_remal_baseline_integrity() -> None:
    """Verify that the authentic Remal baseline granule exists, opens, and matches SHA-256."""
    assert AUTHENTIC_REMAL_HDF5.is_file(), "Authentic Remal HDF5 file missing"
    import hashlib

    h = hashlib.sha256()
    with open(AUTHENTIC_REMAL_HDF5, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    assert h.hexdigest() == EXPECTED_REMAL_SHA

    # Verify HDF5 validity
    with h5py.File(AUTHENTIC_REMAL_HDF5, "r") as h5:
        assert "IMG_TIR1" in h5
        assert "IMG_WV" in h5
        assert "IMG_TIR1_TEMP" in h5
        assert "IMG_WV_TEMP" in h5


def test_truncated_part_files_rejected_by_hdf5() -> None:
    """Verify that partial (.part) downloads fail HDF5 validation and cannot be processed."""
    part_files = list(RAW_DIR.glob("*.part"))
    assert len(part_files) >= 1, "Expected at least one partial .part file for reconciliation"

    for part_file in part_files:
        # Partial files must be recognized as non-HDF5 or truncated
        with pytest.raises(OSError):
            with h5py.File(part_file, "r") as h5:
                _ = list(h5.keys())


def test_granule_reconciliation_json_integrity() -> None:
    """Verify that the forensic granule reconciliation JSON matches verified audit metrics."""
    assert RECONCILIATION_JSON_PATH.is_file()
    with open(RECONCILIATION_JSON_PATH) as f:
        data = json.load(f)

    assert data.get("total_planned_targets") == 6
    assert data.get("completed_downloads") == 0
    assert data.get("partial_downloads") == 2
    assert data.get("failed_downloads") == 1
    assert data.get("unattempted_downloads") == 3

    granules = data.get("granules", [])
    assert len(granules) == 6

    # Verify statuses
    statuses = [g["reconciliation_status"] for g in granules]
    assert statuses.count("PARTIAL_DOWNLOAD") == 2
    assert statuses.count("FAILED") == 1
    assert statuses.count("PLANNED_ONLY") == 3


def test_provenance_and_model_eligibility_invariants() -> None:
    """Verify that partial or planned files evaluate strictly to INELIGIBLE model eligibility."""
    with open(RECONCILIATION_JSON_PATH) as f:
        data = json.load(f)

    for g in data.get("granules", []):
        assert g["registered_in_db"] is False
        assert g["crop_created"] is False
        assert g["model_eligibility"] == "INELIGIBLE"

    baseline = data.get("existing_baseline_authentic_granules", [])[0]
    assert baseline["registered_in_db"] is True
    assert baseline["crop_created"] is True
    assert baseline["model_eligibility"] == "MODEL_ELIGIBLE"
