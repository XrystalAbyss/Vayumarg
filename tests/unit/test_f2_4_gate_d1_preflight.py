"""Unit tests for Milestone F2.4 Gate D1: Balanced Acquisition Selection & First-Batch Preflight."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import (
    DatasetSnapshot,
    SatelliteProcessedCrop,
    Storm,
    TrackObservation,
)

MANIFEST_D1_PATH = Path("reports/F2_4_GATE_D1_APPROVAL_MANIFEST.json")
SCORING_PATH = Path("reports/F2_4_GATE_D1_CANDIDATE_SCORING.json")
CANDIDATE_INV_PATH = Path("reports/F2_4_GATE_D_CANDIDATE_INVENTORY.json")


@pytest.fixture(scope="module")
def db_session():
    """Yield a database session connected to the research database."""
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        yield session


def test_gate_d1_approval_manifest_validation() -> None:
    """Item 11, 12, 15, 16: Verify Gate D1 approval manifest constraints and byte budget."""
    assert MANIFEST_D1_PATH.is_file(), f"Manifest file missing: {MANIFEST_D1_PATH}"
    with open(MANIFEST_D1_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["milestone"] == "F2.4_GATE_D1"
    assert manifest["approval_status"] == "GATE_D1_READY_FOR_OWNER_APPROVAL"

    params = manifest["batch_parameters"]
    assert params["selected_granule_count"] == 3
    assert params["max_transfer_byte_ceiling"] <= 1000000000
    assert params["total_estimated_transfer_bytes"] <= params["max_transfer_byte_ceiling"]
    assert params["concurrency_limit"] == 1
    assert params["http_range_resumption_mandatory"] is True
    assert params["atomic_promotion_mandatory"] is True

    selected = manifest["selected_granules"]
    assert len(selected) == 3

    # Check exact gIds, filenames, and corrected scientific coordinates / pressure labels
    g1, g2, g3 = selected[0], selected[1], selected[2]
    assert g1["storm_name"] == "TAUKTAE"
    assert g1["exact_gid"] == 9293840
    assert g1["exact_filename"] == "3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5"
    assert g1["basin"] == "Arabian Sea (NI)"
    assert g1["primary_imd_label"]["wind_speed_knots"] == 100.0
    assert g1["primary_imd_label"]["category"] == "ESCS"
    assert g1["primary_imd_label"]["latitude"] == 18.5
    assert g1["primary_imd_label"]["longitude"] == 71.5
    assert g1["primary_imd_label"]["central_pressure_hpa"] == 950.0

    assert g2["storm_name"] == "FANI"
    assert g2["exact_gid"] == 7206464
    assert g2["exact_filename"] == "3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5"
    assert g2["basin"] == "Bay of Bengal (NI)"
    assert g2["primary_imd_label"]["wind_speed_knots"] == 105.0
    assert g2["primary_imd_label"]["category"] == "ESCS"
    assert g2["primary_imd_label"]["latitude"] == 19.1
    assert g2["primary_imd_label"]["longitude"] == 85.5
    assert g2["primary_imd_label"]["central_pressure_hpa"] == 945.0

    assert g3["storm_name"] == "FENGAL"
    assert g3["exact_gid"] == 14687507
    assert g3["exact_filename"] == "3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5"
    assert g3["satellite"] == "INSAT-3DS"
    assert g3["primary_imd_label"]["wind_speed_knots"] == 45.0
    assert g3["primary_imd_label"]["category"] == "CS"
    assert g3["primary_imd_label"]["latitude"] == 12.2
    assert g3["primary_imd_label"]["longitude"] == 81.2
    assert g3["primary_imd_label"]["central_pressure_hpa"] == 996.0


def test_candidate_sid_uniqueness_and_overlap() -> None:
    """Item 1, 4, 5: Verify candidate SIDs and exact 15-storm cohort accounting."""
    assert CANDIDATE_INV_PATH.is_file(), f"Inventory missing: {CANDIDATE_INV_PATH}"
    with open(CANDIDATE_INV_PATH, encoding="utf-8") as f:
        inv = json.load(f)

    existing = inv["existing_corpus"]
    candidates = inv["candidate_cohort"]

    existing_sids = {e["sid"] for e in existing}
    candidate_sids = [c["canonical_sid"] for c in candidates]

    assert len(existing) == 4
    assert len(candidates) == 14

    unique_candidate_sids = set(candidate_sids)
    assert len(unique_candidate_sids) == 12

    # Exactly 1 existing SID repeated in candidate cohort (REMAL_DEV)
    repeated_existing = unique_candidate_sids.intersection(existing_sids)
    assert len(repeated_existing) == 1
    assert "2024145N14087" in repeated_existing

    # Exactly 11 newly introduced SIDs
    new_sids = unique_candidate_sids - existing_sids
    assert len(new_sids) == 11

    # Full cohort unique storms: exactly 15
    total_unique_sids = existing_sids.union(unique_candidate_sids)
    assert len(total_unique_sids) == 15

    # Check verified REMAL gId
    remal_item = next(e for e in existing if e["storm_name"] == "REMAL")
    assert remal_item["gid"] == "13623453"


def test_candidate_scoring_reproducibility() -> None:
    """Item 10: Verify multi-objective candidate scoring calculations and 100-point sum."""
    assert SCORING_PATH.is_file(), f"Scoring missing: {SCORING_PATH}"
    with open(SCORING_PATH, encoding="utf-8") as f:
        scoring_data = json.load(f)

    # Check scoring weights sum to strictly 100
    weights = scoring_data["scoring_weights"]
    component_weights_sum = sum(v for k, v in weights.items() if k != "total_max_points")
    assert component_weights_sum == 100
    assert weights["total_max_points"] == 100

    ranked = scoring_data["ranked_candidates"]
    assert len(ranked) == 14

    for c in ranked:
        scores = c["scores"]
        expected_total = sum(scores.values())
        assert c["total_score"] == expected_total
        assert c["total_score"] <= 100

    # Verify top ranked are TAUKTAE, FENGAL, ASNA, FANI, MOCHA
    top_names = [c["storm_name"] for c in ranked[:5]]
    assert "TAUKTAE" in top_names
    assert "FENGAL" in top_names
    assert "FANI" in top_names


def test_database_label_validity_for_batch_d1(db_session: Session) -> None:
    """Item 6, 7, 8: Verify ground-truth best-track observations in PostgreSQL for Batch D1."""
    # 1. TAUKTAE (2021-05-17 00:00 UTC)
    st_tauktae = db_session.execute(
        select(Storm).where(Storm.canonical_name == "TAUKTAE")
    ).scalar_one_or_none()
    if st_tauktae is None:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires populated historical research database with TAUKTAE, FANI, and FENGAL"
        )
    obs_tauktae = (
        db_session.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st_tauktae.id,
                TrackObservation.observation_time_utc == datetime(2021, 5, 17, 0, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )

    imd_t = (
        next((o for o in obs_t if o.source_agency == "IMD"), None)
        if (obs_t := obs_tauktae)
        else None
    )
    assert imd_t is not None
    assert imd_t.wind_speed_knots == 100.0
    assert imd_t.imd_category == "ESCS"
    assert imd_t.averaging_period == "3-min"

    # 2. FANI (2019-05-03 00:00 UTC)
    st_fani = db_session.execute(select(Storm).where(Storm.canonical_name == "FANI")).scalar_one()
    obs_fani = (
        db_session.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st_fani.id,
                TrackObservation.observation_time_utc == datetime(2019, 5, 3, 0, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )

    imd_f = next((o for o in obs_fani if o.source_agency == "IMD"), None)
    assert imd_f is not None
    assert imd_f.wind_speed_knots == 105.0
    assert imd_f.imd_category == "ESCS"
    assert imd_f.averaging_period == "3-min"

    # 3. FENGAL (2024-11-30 00:00 UTC)
    st_fengal = db_session.execute(
        select(Storm).where(Storm.canonical_name == "FENGAL")
    ).scalar_one()
    obs_fengal = (
        db_session.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st_fengal.id,
                TrackObservation.observation_time_utc == datetime(2024, 11, 30, 0, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )

    imd_fe = next((o for o in obs_fengal if o.source_agency == "IMD"), None)
    assert imd_fe is not None
    assert imd_fe.wind_speed_knots == 45.0
    assert imd_fe.imd_category == "CS"
    assert imd_fe.averaging_period == "3-min"


def test_f1_1_freeze_preservation_and_isolation(db_session: Session) -> None:
    """Item 17, 18: Verify F1.1 historical baseline preservation and synthetic isolation."""
    total_storms = db_session.execute(select(Storm)).scalars().all()
    if len(total_storms) == 0:
        pytest.skip(
            "NOT_EXECUTED_PRIVATE_DATA: Requires pre-populated 1,860-storm historical research database"
        )
    total_obs = db_session.execute(select(TrackObservation)).scalars().all()
    assert len(total_storms) == 1860
    assert len(total_obs) == 104374

    snap = db_session.execute(select(DatasetSnapshot)).scalar_one()
    assert (
        snap.manifest_sha256 == "441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107"
    )

    # Synthetic crops remain quarantined
    syn_crops = (
        db_session.execute(
            select(SatelliteProcessedCrop).where(
                SatelliteProcessedCrop.verification_status == "SYNTHETIC_FIXTURE"
            )
        )
        .scalars()
        .all()
    )
    assert len(syn_crops) == 12
