"""Unit tests for Milestone F2.4 Gate C readiness, scientific label audits, and sensor contracts."""

import json
from pathlib import Path

import h5py
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import (
    DatasetSnapshot,
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteTrackAssociation,
    Storm,
    TrackObservation,
)

MANIFEST_PATH = Path("reports/F2_4_GATE_C_ACQUISITION_MANIFEST.json")
DANA_HDF5 = Path("data/raw/satellite/insat_real/3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5")


def test_gate_c_acquisition_manifest_validation() -> None:
    """Verify that Gate C acquisition manifest complies with all strict constraints."""
    assert MANIFEST_PATH.is_file(), f"Manifest file missing: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["milestone"] == "F2.4_GATE_C"
    assert manifest["batch_approval_status"] == "GATE_C_BATCH_PENDING_OWNER_APPROVAL"

    budget = manifest["budget_constraints"]
    assert budget["max_granules"] == 2
    assert budget["max_transfer_mb"] <= 1000.0
    assert budget["max_concurrent_transfers"] == 1

    candidates = manifest["candidates"]
    assert len(candidates) == 2

    c_a, c_b = candidates[0], candidates[1]
    assert c_a["candidate_id"] == "GATE_C_CANDIDATE_A"
    assert c_a["storm_name"] == "AMPHAN"
    assert c_a["basin"] == "Bay of Bengal"
    assert c_a["mosdac_gid"] == 8353650
    assert c_a["exact_filename"] == "3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5"
    assert c_a["primary_imd_label"]["available"] is True
    assert c_a["primary_imd_label"]["wind_speed_knots"] == 95.0
    assert c_a["primary_imd_label"]["category"] == "ESCS"
    assert c_a["primary_imd_label"]["temporal_offset_minutes"] == 2.0

    assert c_b["candidate_id"] == "GATE_C_CANDIDATE_B"
    assert c_b["storm_name"] == "BIPARJOY"
    assert c_b["basin"] == "Arabian Sea"
    assert c_b["mosdac_gid"] == 11789302
    assert c_b["exact_filename"] == "3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5"
    assert c_b["primary_imd_label"]["available"] is True
    assert c_b["primary_imd_label"]["wind_speed_knots"] == 85.0
    assert c_b["primary_imd_label"]["category"] == "VSCS"
    assert c_b["primary_imd_label"]["temporal_offset_minutes"] == 2.0


def test_dana_late_stage_label_audit_and_eligibility() -> None:
    """Verify DANA late-stage label audit and multi-dimensional model eligibility."""
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        crop = s.execute(
            select(SatelliteProcessedCrop).where(SatelliteProcessedCrop.storage_uri.like("%DANA%"))
        ).scalar_one()

        qc = crop.quality_control_flags or {}
        assert "model_eligibility" in qc, "model_eligibility missing from DANA crop QC flags"
        me = qc["model_eligibility"]

        # Valid research roles
        assert me["general_atmospheric_research"] is True
        assert me["post_landfall_weakening_analysis"] is True
        assert me["agency_conditioned_jtwc_intensity"] is True

        # Ineligible roles: No primary IMD cyclone grade past documented WML boundary
        assert me["primary_imd_category_classification"] is False
        assert me["primary_imd_wind_intensity_regression"] is False
        assert len(me["ineligibility_reasons"]) > 0

        # Verification status must remain REAL_VERIFIED
        assert crop.verification_status == "REAL_VERIFIED"


@pytest.mark.skipif(not DANA_HDF5.is_file(), reason="DANA HDF5 file not present on disk")
def test_insat3ds_wv_delivered_grid_vs_native_instrument_resolution() -> None:
    """Verify that INSAT-3DS L1B metadata reports 8 km instrument resolution on a 4 km grid."""
    with h5py.File(DANA_HDF5, "r") as f:
        assert "IMG_WV" in f
        wv_ds = f["IMG_WV"]
        # Product delivered grid shape matches TIR-1
        assert wv_ds.shape == (1, 2816, 2805)
        # Instrument nominal optical resolution attribute is explicitly 8 km
        res_attr = float(wv_ds.attrs.get("resolution", [0.0])[0])
        assert res_attr == 8.0
        assert wv_ds.attrs.get("resolution_unit", b"").decode().strip() == "km"

        # Coordinates attribute references common Latitude/Longitude grid
        coord_attr = wv_ds.attrs.get("coordinates", b"").decode()
        assert "Latitude Longitude" in coord_attr


def test_real_and_synthetic_provenance_isolation_in_db() -> None:
    """Verify that REAL_VERIFIED and SYNTHETIC_FIXTURE database rows remain segregated."""
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        # Granules
        real_granules = (
            s.execute(
                select(SatelliteGranule).where(
                    SatelliteGranule.verification_status == "REAL_VERIFIED"
                )
            )
            .scalars()
            .all()
        )
        assert len(real_granules) == 4
        real_names = {g.granule_name for g in real_granules}
        assert "3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5" in real_names
        assert "3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5" in real_names
        assert "3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5" in real_names
        assert "3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5" in real_names

        synth_granules = (
            s.execute(
                select(SatelliteGranule).where(
                    SatelliteGranule.verification_status == "SYNTHETIC_FIXTURE"
                )
            )
            .scalars()
            .all()
        )
        assert len(synth_granules) == 1

        # Real crops
        real_crops = (
            s.execute(
                select(SatelliteProcessedCrop).where(
                    SatelliteProcessedCrop.verification_status == "REAL_VERIFIED"
                )
            )
            .scalars()
            .all()
        )
        assert len(real_crops) == 4

        # Real associations
        real_assocs = (
            s.execute(
                select(SatelliteTrackAssociation).where(
                    SatelliteTrackAssociation.verification_status == "REAL_VERIFIED"
                )
            )
            .scalars()
            .all()
        )
        assert len(real_assocs) == 10


def test_f1_1_frozen_dataset_and_storm_count_preservation() -> None:
    """Verify that historical storms, observations, and frozen snapshots remain untouched."""
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        # Check snapshot
        snap = s.execute(
            select(DatasetSnapshot).where(
                DatasetSnapshot.snapshot_name == "vayumarg-nio-ibtracs-f1.1-freeze"
            )
        ).scalar_one()
        assert snap.transformation_version == "f1.1"
        assert (
            snap.manifest_sha256
            == "441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107"
        )
        assert snap.total_samples == 104374

        # Check total storms and observations
        storm_count = s.execute(select(func.count(Storm.id))).scalar_one()
        assert storm_count == 1860

        obs_count = s.execute(select(func.count(TrackObservation.id))).scalar_one()
        assert obs_count == 104374
