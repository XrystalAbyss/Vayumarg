"""Unit tests for Milestone F2.4 Gate C1R: Scientific Metadata Closure and Gate D Preflight."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import (
    DatasetSnapshot,
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteTrackAssociation,
    Storm,
    StormAlias,
    TrackObservation,
)

LEDGER_PATH = Path("reports/F2_4_GATE_C1R_SCIENTIFIC_LEDGER.json")
GATE_D_INVENTORY_PATH = Path("reports/F2_4_GATE_D_CANDIDATE_INVENTORY.json")
GATE_D_PREFLIGHT_PATH = Path("reports/F2_4_GATE_D_ACQUISITION_PREFLIGHT.json")


@pytest.fixture(scope="module")
def db_session():
    """Yield a database session connected to the research database."""
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        yield session


def test_biparjoy_canonical_sid_and_alias_resolution(db_session: Session) -> None:
    """Item 1 & 2: Verify Cyclone BIPARJOY resolves strictly to canonical SID 2023156N10067."""
    storm = db_session.execute(
        select(Storm).where(Storm.canonical_name == "BIPARJOY", Storm.season_year == 2023)
    ).scalar_one_or_none()
    if storm is None:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires populated 1,860-storm historical research database with Cyclone BIPARJOY"
        )

    aliases = (
        db_session.execute(select(StormAlias).where(StormAlias.storm_id == storm.id))
        .scalars()
        .all()
    )

    alias_dict = {a.source_agency: a.agency_storm_id for a in aliases}
    assert "IBTRACS" in alias_dict, "IBTrACS alias missing for BIPARJOY"
    assert alias_dict["IBTRACS"] == "2023156N10067", (
        f"Expected canonical SID 2023156N10067, found {alias_dict['IBTRACS']}"
    )
    assert alias_dict.get("JTWC") == "IO022023"


def test_incorrect_biparjoy_sid_rejection(db_session: Session) -> None:
    """Item 3: Verify erroneous SID 2023157N13066 does NOT exist in any database table."""
    bad_alias = db_session.execute(
        select(StormAlias).where(StormAlias.agency_storm_id == "2023157N13066")
    ).all()
    assert len(bad_alias) == 0, "Erroneous SID 2023157N13066 unexpectedly found in storm_aliases!"

    # Also verify raw CSV does not contain it
    raw_csv = Path("data/raw/ibtracs_ni_v04r01.csv")
    if raw_csv.is_file():
        content = raw_csv.read_text(encoding="utf-8", errors="ignore")
        assert "2023157N13066" not in content, "Erroneous SID found in raw IBTrACS CSV!"


def test_crop_to_storm_foreign_key_integrity(db_session: Session) -> None:
    """Item 4: Verify crop-to-storm foreign key relationships for all 4 authentic crops."""
    crops = (
        db_session.execute(
            select(SatelliteProcessedCrop).where(
                SatelliteProcessedCrop.verification_status == "REAL_VERIFIED"
            )
        )
        .scalars()
        .all()
    )

    if len(crops) < 4:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires 4 authentic REAL_VERIFIED satellite crops in research database"
        )

    assert len(crops) == 4, f"Expected 4 real verified crops, found {len(crops)}"
    for crop in crops:
        storm = db_session.execute(select(Storm).where(Storm.id == crop.storm_id)).scalar_one()
        granule = db_session.execute(
            select(SatelliteGranule).where(SatelliteGranule.id == crop.granule_id)
        ).scalar_one()
        assert storm is not None
        assert granule is not None
        assert crop.quality_control_flags is not None


def test_dana_task_specific_eligibility(db_session: Session) -> None:
    """Item 5: Verify DANA task-specific eligibility in metadata flags and DB associations."""
    dana_crop = db_session.execute(
        select(SatelliteProcessedCrop).where(
            SatelliteProcessedCrop.verification_status == "REAL_VERIFIED",
            SatelliteProcessedCrop.storage_uri.like("%DANA%"),
        )
    ).scalar_one_or_none()

    if dana_crop is None:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires authentic DANA REAL_VERIFIED satellite crop in research database"
        )

    qc = dana_crop.quality_control_flags or {}
    elig = qc.get("model_eligibility", {})

    # Ineligible for primary IMD targets
    assert elig.get("primary_imd_category_classification") is False
    assert elig.get("primary_imd_wind_intensity_regression") is False

    # Eligible for weakening analysis and JTWC
    assert elig.get("post_landfall_weakening_analysis") is True
    assert elig.get("agency_conditioned_jtwc_intensity") is True
    assert elig.get("general_atmospheric_research") is True

    # Check associations for DANA: ZERO IMD associations
    assocs = (
        db_session.execute(
            select(SatelliteTrackAssociation).where(
                SatelliteTrackAssociation.crop_id == dana_crop.id
            )
        )
        .scalars()
        .all()
    )

    agencies = []
    for a in assocs:
        obs = db_session.execute(
            select(TrackObservation).where(TrackObservation.id == a.track_observation_id)
        ).scalar_one()
        agencies.append(obs.source_agency)

    assert "IMD" not in agencies, "Unexpected IMD association linked to post-landfall DANA!"
    assert "JTWC" in agencies


def test_difference_between_associations_and_independent_samples(db_session: Session) -> None:
    """Item 6: Verify that 10 associations correspond to strictly 4 unique physical image samples."""
    real_crops = (
        db_session.execute(
            select(SatelliteProcessedCrop).where(
                SatelliteProcessedCrop.verification_status == "REAL_VERIFIED"
            )
        )
        .scalars()
        .all()
    )

    if len(real_crops) < 4:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires 4 authentic REAL_VERIFIED satellite crops in research database"
        )

    real_assocs = (
        db_session.execute(
            select(SatelliteTrackAssociation).where(
                SatelliteTrackAssociation.verification_status == "REAL_VERIFIED"
            )
        )
        .scalars()
        .all()
    )

    # 4 crops, 10 associations
    assert len(real_crops) == 4
    assert len(real_assocs) == 10

    # Ensure grouping by crop_id yields exactly 4 independent samples
    unique_crop_ids = {a.crop_id for a in real_assocs}
    assert len(unique_crop_ids) == 4


def test_imd_and_jtwc_averaging_period_preservation(db_session: Session) -> None:
    """Item 7: Verify strict preservation of averaging periods (IMD 3-min vs JTWC 1-min)."""
    assocs = (
        db_session.execute(
            select(SatelliteTrackAssociation).where(
                SatelliteTrackAssociation.verification_status == "REAL_VERIFIED"
            )
        )
        .scalars()
        .all()
    )

    if not assocs:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires authentic REAL_VERIFIED satellite track associations in research database"
        )

    for a in assocs:
        obs = db_session.execute(
            select(TrackObservation).where(TrackObservation.id == a.track_observation_id)
        ).scalar_one()

        if obs.source_agency == "IMD":
            assert obs.averaging_period == "3-min", f"IMD observation {obs.id} must be 3-min"
        elif obs.source_agency == "JTWC":
            assert obs.averaging_period == "1-min", f"JTWC observation {obs.id} must be 1-min"


def test_consensus_as_duplicate_detection(db_session: Session) -> None:
    """Item 8: Verify that IBTRACS WMO consensus observations duplicate IMD observations."""
    # Check for AMPHAN and BIPARJOY
    for storm_name in ["AMPHAN", "BIPARJOY"]:
        storm = db_session.execute(
            select(Storm).where(Storm.canonical_name == storm_name)
        ).scalar_one_or_none()
        if storm is None:
            pytest.skip(
                f"NOT_EXECUTED_PRIVATE_DATA: Requires populated historical research database with {storm_name}"
            )
        crop = db_session.execute(
            select(SatelliteProcessedCrop).where(
                SatelliteProcessedCrop.storm_id == storm.id,
                SatelliteProcessedCrop.verification_status == "REAL_VERIFIED",
            )
        ).scalar_one_or_none()
        if crop is None:
            pytest.skip(
                f"NOT_EXECUTED_PRIVATE_DATA: Requires REAL_VERIFIED crop for {storm_name} in research database"
            )

        assocs = (
            db_session.execute(
                select(SatelliteTrackAssociation).where(
                    SatelliteTrackAssociation.crop_id == crop.id
                )
            )
            .scalars()
            .all()
        )

        obs_by_agency = {}
        for a in assocs:
            obs = db_session.execute(
                select(TrackObservation).where(TrackObservation.id == a.track_observation_id)
            ).scalar_one()
            obs_by_agency[obs.source_agency] = obs

        assert "IMD" in obs_by_agency
        assert "IBTRACS" in obs_by_agency
        imd_obs = obs_by_agency["IMD"]
        ibtracs_obs = obs_by_agency["IBTRACS"]

        # In Basin NI, IBTrACS WMO values match IMD RSMC New Delhi values exactly
        assert ibtracs_obs.wind_speed_knots == imd_obs.wind_speed_knots
        assert ibtracs_obs.central_pressure_hpa == imd_obs.central_pressure_hpa
        assert ibtracs_obs.wmo_agency == "newdelhi"


def test_scientific_ledger_fields_and_integrity() -> None:
    """Item 9 & 10: Verify the generated machine-readable scientific ledger."""
    assert LEDGER_PATH.is_file(), f"Ledger file missing: {LEDGER_PATH}"
    with open(LEDGER_PATH, encoding="utf-8") as f:
        ledger = json.load(f)

    assert ledger["milestone"] == "F2.4_GATE_C1R"
    assert ledger["total_authentic_crops"] == 4
    crops = ledger["crops"]
    assert len(crops) == 4

    for crop in crops:
        assert crop["crop_id"] is not None
        assert crop["canonical_storm_sid"] in [
            "2024145N14087",
            "2024295N15092",
            "2020136N10088",
            "2023156N10067",
        ]
        assert crop["crop_extent_km"] == 800.0
        assert crop["target_grid_spacing_km"] == 4.0
        assert crop["source_provenance_status"] == "REAL_VERIFIED"
        assert crop["radiometric_qc_status"] == "PASS_GRADE_A"

        # Check valid fractions are 100% or close to 1.0
        for ch, v_frac in crop["valid_fraction_by_channel"].items():
            assert v_frac >= 0.9999, f"Channel {ch} has low valid fraction {v_frac}"


def test_crop_geolocation_residuals(db_session: Session) -> None:
    """Item 11: Verify spatial offsets and distinguish residuals from meteorological uncertainty."""
    assocs = (
        db_session.execute(
            select(SatelliteTrackAssociation).where(
                SatelliteTrackAssociation.verification_status == "REAL_VERIFIED"
            )
        )
        .scalars()
        .all()
    )

    if not assocs:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires authentic REAL_VERIFIED satellite track associations in research database"
        )

    for a in assocs:
        # Spatial offset to best track center must be strictly bounded <= 100 km
        assert a.spatial_offset_km <= 100.0
        assert a.temporal_offset_minutes <= 60.0


def test_gate_d_candidate_inventory_and_preflight() -> None:
    """Item 12 & 13: Verify Gate D candidate inventory structure and preflight constraints."""
    assert GATE_D_INVENTORY_PATH.is_file(), f"Inventory missing: {GATE_D_INVENTORY_PATH}"
    assert GATE_D_PREFLIGHT_PATH.is_file(), f"Preflight missing: {GATE_D_PREFLIGHT_PATH}"

    with open(GATE_D_INVENTORY_PATH, encoding="utf-8") as f:
        inv = json.load(f)

    with open(GATE_D_PREFLIGHT_PATH, encoding="utf-8") as f:
        pre = json.load(f)

    assert inv["planning_ceiling"]["cohort_total_granules"] == 18
    assert inv["planning_ceiling"]["already_acquired_granules"] == 4
    assert inv["planning_ceiling"]["candidate_granules_planned"] == 14
    assert len(inv["candidate_cohort"]) == 14

    # Ensure no candidate gId duplicates
    gids = [c["mosdac_gid"] for c in inv["candidate_cohort"]]
    assert len(gids) == len(set(gids)), "Duplicate MOSDAC gIds detected in candidate cohort!"

    # Ensure preflight respects batching
    batches = pre["proposed_batch_execution_plan"]
    for b in batches:
        assert b["granule_count"] in [1, 2, 3], f"Batch {b['batch_id']} exceeds max batch size of 3"


def test_f1_1_freeze_and_database_isolation(db_session: Session) -> None:
    """Item 14, 15, 16: Verify historical F1.1 baseline freeze and synthetic isolation."""
    # Check total storms and observations
    total_storms = db_session.execute(select(Storm)).scalars().all()
    if len(total_storms) == 0:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires pre-populated 1,860-storm historical research database"
        )
    total_obs = db_session.execute(select(TrackObservation)).scalars().all()
    assert len(total_storms) == 1860
    assert len(total_obs) == 104374

    # Check snapshot hash
    snapshot = db_session.execute(select(DatasetSnapshot)).scalar_one()
    assert (
        snapshot.manifest_sha256
        == "441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107"
    )

    # Check synthetic isolation
    synthetic_crops = (
        db_session.execute(
            select(SatelliteProcessedCrop).where(
                SatelliteProcessedCrop.verification_status == "SYNTHETIC_FIXTURE"
            )
        )
        .scalars()
        .all()
    )
    assert len(synthetic_crops) == 12
