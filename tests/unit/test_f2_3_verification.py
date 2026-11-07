"""Unit tests for Milestone F2.3: acquisition manifest, budget, governance, and preprocessing."""

import json
from pathlib import Path

import numpy as np

from vayumarg.contracts.enums import (
    ModelEligibility,
    ProvenanceStatus,
    ScientificQualityStatus,
)
from vayumarg.satellite.crop_engine import (
    bilinear_resample_2d,
)

MANIFEST_PATH = Path("reports/F2_3_ACQUISITION_MANIFEST.json")
FREEZE_MANIFEST_PATH = Path("data/manifests/vayumarg_f1_1_freeze_manifest.json")
EXPECTED_FREEZE_SHA = "441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107"


def test_acquisition_manifest_integrity_and_budget() -> None:
    """Verify that the acquisition manifest satisfies all safety bounds."""
    assert MANIFEST_PATH.is_file(), "Manifest file missing"
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    granules = manifest.get("granules", [])
    # 1. Budget constraint: max 6 granules
    assert len(granules) <= 6
    assert manifest.get("budget_max_granules") == 6
    assert manifest.get("budget_max_mb") <= 2000.0

    # 2. Check each granule has unique numeric gId and unique filename
    gids = [g["granule_gid"] for g in granules]
    assert len(set(gids)) == len(gids), "Duplicate gId detected in manifest"
    for gid in gids:
        assert gid.isdigit(), f"Invalid non-numeric gId: {gid}"

    filenames = [g["expected_identifier"] for g in granules]
    assert len(set(filenames)) == len(filenames), "Duplicate filename in manifest"

    # 3. Sum of approximate sizes must be <= 2000 MB
    total_est_mb = sum(g.get("approx_size_mb", 0.0) for g in granules)
    assert total_est_mb <= 2000.0


def test_frozen_snapshot_preservation() -> None:
    """Verify that F1.1 frozen snapshot manifest is strictly preserved."""
    assert FREEZE_MANIFEST_PATH.is_file()
    import hashlib

    h = hashlib.sha256()
    with open(FREEZE_MANIFEST_PATH, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    assert h.hexdigest() == EXPECTED_FREEZE_SHA


def test_normalized_bilinear_resampling_edge_cases() -> None:
    """Verify normalized bilinear resampling handles all-invalid regions and single pixel cases."""
    # 1. All-invalid array should evaluate strictly to NaN
    all_nan = np.full((5, 5), np.nan, dtype=float)
    res = bilinear_resample_2d(all_nan, (10, 10))
    assert np.all(np.isnan(res))

    # 2. Single valid pixel in 1x1 array
    single_val = np.array([[220.0]], dtype=float)
    res_single = bilinear_resample_2d(single_val, (5, 5))
    assert res_single.shape == (5, 5)
    assert np.all(np.isclose(res_single, 220.0))

    # 3. Identity shape
    same = np.array([[210.0, 220.0], [230.0, 240.0]], dtype=float)
    mask = np.array([[True, True], [True, False]], dtype=bool)
    res_same = bilinear_resample_2d(same, (2, 2), valid_mask=mask)
    assert np.isclose(res_same[0, 0], 210.0)
    assert np.isnan(res_same[1, 1])


def test_governance_status_enums() -> None:
    """Verify that provenance, quality, and eligibility enums are correctly defined."""
    assert ProvenanceStatus.REAL_VERIFIED.value == "REAL_VERIFIED"
    assert ProvenanceStatus.SYNTHETIC_FIXTURE.value == "SYNTHETIC_FIXTURE"

    assert ScientificQualityStatus.RADIOMETRY_VALIDATED.value == "RADIOMETRY_VALIDATED"
    assert ScientificQualityStatus.CALIBRATION_CLAMPED.value == "CALIBRATION_CLAMPED"

    assert ModelEligibility.MODEL_ELIGIBLE.value == "MODEL_ELIGIBLE"
    assert ModelEligibility.SYNTHETIC_FIXTURE.value == "SYNTHETIC_FIXTURE"
