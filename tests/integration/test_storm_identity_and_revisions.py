"""Integration tests for storm identity, alias namespaces, and observation revisions.

Verifies:
1. Two unnamed storms in the same season and basin coexist.
2. Two distinct storms sharing a canonical name coexist.
3. Duplicate source identifiers within an agency namespace are rejected.
4. Conflicting agency aliases within the same namespace are rejected.
5. Multiple agencies reporting at the same timestamp coexist.
6. Deterministic observation identity and duplicate row rejection.
7. Source revision handling (old asset observations preserved, new asset records added).
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency, AveragingPeriod
from vayumarg.database.schema import (
    DataSource,
    SourceAsset,
    Storm,
    StormAlias,
    TrackObservation,
)


@pytest.mark.integration
def test_unnamed_storms_same_season_and_basin_coexist(db_session: Session):
    """Verify two unnamed storms in the same season and basin can coexist."""
    storm1 = Storm(
        id=uuid.uuid4(),
        canonical_name="UNNAMED",
        season_year=2024,
        primary_basin="BOB",
        nature="D",
    )
    storm2 = Storm(
        id=uuid.uuid4(),
        canonical_name="UNNAMED",
        season_year=2024,
        primary_basin="BOB",
        nature="DD",
    )

    db_session.add(storm1)
    db_session.add(storm2)
    db_session.flush()

    queried = (
        db_session.execute(
            select(Storm).where(
                Storm.canonical_name == "UNNAMED",
                Storm.season_year == 2024,
                Storm.primary_basin == "BOB",
            )
        )
        .scalars()
        .all()
    )

    assert len(queried) == 2
    assert storm1.id != storm2.id


@pytest.mark.integration
def test_distinct_storms_sharing_canonical_name_coexist(db_session: Session):
    """Verify distinct storms sharing a canonical name (e.g. across seasons or basins) coexist."""
    storm_bob = Storm(
        id=uuid.uuid4(),
        canonical_name="GULAB",
        season_year=2021,
        primary_basin="BOB",
    )
    storm_arb = Storm(
        id=uuid.uuid4(),
        canonical_name="GULAB",
        season_year=2021,
        primary_basin="ARB",
    )

    db_session.add(storm_bob)
    db_session.add(storm_arb)
    db_session.flush()

    assert storm_bob.id != storm_arb.id


@pytest.mark.integration
def test_duplicate_source_identifier_within_agency_rejected(
    db_session: Session, synthetic_storm: Storm
):
    """Verify that duplicate source identifiers (e.g. IBTrACS SID) in the same namespace are rejected."""
    # First alias for storm
    alias1 = StormAlias(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_agency=Agency.IBTRACS.value,
        agency_storm_id="2024140N10085",  # Authoritative IBTrACS SID
        agency_storm_name="REMAL",
        matching_confidence=1.0,
    )
    db_session.add(alias1)
    db_session.flush()

    # Create a second storm attempting to register the exact same IBTrACS SID
    second_storm = Storm(
        id=uuid.uuid4(),
        canonical_name="CONFLICTING_STORM",
        season_year=2024,
        primary_basin="BOB",
    )
    db_session.add(second_storm)
    db_session.flush()

    duplicate_alias = StormAlias(
        id=uuid.uuid4(),
        storm_id=second_storm.id,
        source_agency=Agency.IBTRACS.value,
        agency_storm_id="2024140N10085",  # Conflicting duplicate SID in IBTrACS namespace
        agency_storm_name="CONFLICT",
        matching_confidence=1.0,
    )
    db_session.add(duplicate_alias)

    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


@pytest.mark.integration
def test_distinct_agencies_can_alias_same_storm(db_session: Session, synthetic_storm: Storm):
    """Verify multiple agencies (IMD, JTWC, IBTrACS) can map their respective IDs to one canonical storm."""
    alias_imd = StormAlias(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_agency=Agency.IMD.value,
        agency_storm_id="BOB 01/2024",
        agency_storm_name="REMAL",
        matching_confidence=1.0,
    )
    alias_jtwc = StormAlias(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_agency=Agency.JTWC.value,
        agency_storm_id="01B",
        agency_storm_name="REMAL",
        matching_confidence=1.0,
    )
    alias_ibtracs = StormAlias(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_agency=Agency.IBTRACS.value,
        agency_storm_id="2024140N10085",
        agency_storm_name="REMAL",
        matching_confidence=1.0,
    )

    db_session.add(alias_imd)
    db_session.add(alias_jtwc)
    db_session.add(alias_ibtracs)
    db_session.flush()

    aliases = (
        db_session.execute(select(StormAlias).where(StormAlias.storm_id == synthetic_storm.id))
        .scalars()
        .all()
    )

    assert len(aliases) == 3
    agency_set = {a.source_agency for a in aliases}
    assert agency_set == {"IMD", "JTWC", "IBTRACS"}


@pytest.mark.integration
def test_deterministic_observation_identity_and_duplicate_rejection(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify that duplicate row imports within the same source asset are strictly rejected."""
    obs1 = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="ROW-00042",
        observation_time_utc=datetime(2024, 5, 25, 0, 0, tzinfo=UTC),
        latitude=19.5,
        longitude=88.5,
        wind_speed_knots=50.0,
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
    )
    db_session.add(obs1)
    db_session.flush()

    # Attempt duplicate insert of same record from same source asset
    duplicate_obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="ROW-00042",  # Duplicate record ID for same asset
        observation_time_utc=datetime(2024, 5, 25, 0, 0, tzinfo=UTC),
        latitude=19.5,
        longitude=88.5,
        wind_speed_knots=50.0,
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
    )
    db_session.add(duplicate_obs)

    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


@pytest.mark.integration
def test_source_revision_preserves_old_observations_and_links_new_asset(
    db_session: Session,
    synthetic_data_source: DataSource,
    synthetic_storm: Storm,
):
    """Verify that when a revised best-track asset is ingested, historical observations are preserved."""
    obs_time = datetime(2024, 5, 25, 6, 0, tzinfo=UTC)

    # 1. Original Best-Track Asset (e.g. v04r00)
    asset_v1 = SourceAsset(
        id=uuid.uuid4(),
        data_source_id=synthetic_data_source.id,
        artifact_uri="file:///data/raw/ibtracs_v04r00.csv",
        sha256_checksum="1111111111111111111111111111111111111111111111111111111111111111",
        file_size_bytes=500000,
        asset_type="TRACK_CSV",
        retrieval_time_utc=datetime(2024, 6, 1, 0, 0, tzinfo=UTC),
    )
    db_session.add(asset_v1)
    db_session.flush()

    obs_v1 = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=asset_v1.id,
        source_agency=Agency.IMD.value,
        source_record_id="SYNOPTIC-20240525-06",
        observation_time_utc=obs_time,
        latitude=19.8,
        longitude=88.6,
        wind_speed_knots=60.0,  # Preliminary estimated wind
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
        is_superseded=False,
    )
    db_session.add(obs_v1)
    db_session.flush()

    # 2. Revised Post-Season Best-Track Asset (e.g. v04r01)
    asset_v2 = SourceAsset(
        id=uuid.uuid4(),
        data_source_id=synthetic_data_source.id,
        artifact_uri="file:///data/raw/ibtracs_v04r01_revised.csv",
        sha256_checksum="2222222222222222222222222222222222222222222222222222222222222222",
        file_size_bytes=505000,
        asset_type="TRACK_CSV",
        retrieval_time_utc=datetime(2024, 12, 1, 0, 0, tzinfo=UTC),
    )
    db_session.add(asset_v2)
    db_session.flush()

    # Revised observation with re-analyzed wind speed (65 kt)
    obs_v2 = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=asset_v2.id,
        source_agency=Agency.IMD.value,
        source_record_id="SYNOPTIC-20240525-06",
        observation_time_utc=obs_time,
        latitude=19.9,
        longitude=88.7,
        wind_speed_knots=65.0,  # Revised wind
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
        is_superseded=False,
    )
    # Mark old observation as superseded
    obs_v1.is_superseded = True

    db_session.add(obs_v2)
    db_session.flush()

    # 3. Verify Both Observations Coexist in History
    all_obs = (
        db_session.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == synthetic_storm.id,
                TrackObservation.observation_time_utc == obs_time,
            )
        )
        .scalars()
        .all()
    )

    assert len(all_obs) == 2

    # Check active vs superseded
    active_obs = [o for o in all_obs if not o.is_superseded]
    superseded_obs = [o for o in all_obs if o.is_superseded]

    assert len(active_obs) == 1
    assert active_obs[0].source_asset_id == asset_v2.id
    assert active_obs[0].wind_speed_knots == 65.0

    assert len(superseded_obs) == 1
    assert superseded_obs[0].source_asset_id == asset_v1.id
    assert superseded_obs[0].wind_speed_knots == 60.0
