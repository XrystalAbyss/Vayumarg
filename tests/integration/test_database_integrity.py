"""Real PostgreSQL/PostGIS integration test suite for Vayumarg F0 foundation.

Validates schema constraints, geospatial types, check constraints, foreign key cascades,
duplicate source protection, and transaction rollback mechanics.
All test records are synthetic test fixtures strictly labeled as synthetic.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency, AveragingPeriod, IMDCategory, WindUnit
from vayumarg.database.schema import (
    DataSource,
    SourceAsset,
    Storm,
    TrackObservation,
)


@pytest.mark.integration
def test_postgis_extension_available(db_session: Session):
    """Verify PostGIS extension functions on real PostgreSQL."""
    result = db_session.execute(text("SELECT PostGIS_Version();")).scalar()
    assert result is not None
    assert "3." in str(result)


@pytest.mark.integration
def test_synthetic_data_insertion_and_foreign_keys(
    db_session: Session,
    synthetic_data_source: DataSource,
    synthetic_source_asset: SourceAsset,
    synthetic_storm: Storm,
):
    """Verify valid insertion of synthetic cyclone observation and FK integrity."""
    obs_id = uuid.uuid4()
    obs = TrackObservation(
        id=obs_id,
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="SYNTH-OBS-001",
        observation_time_utc=datetime(2024, 5, 20, 6, 0, 0, tzinfo=UTC),
        latitude=16.5,
        longitude=87.5,
        geom=text("ST_SetSRID(ST_MakePoint(87.5, 16.5), 4326)"),
        wind_speed_knots=75.0,
        original_wind_speed=75.0,
        original_wind_unit=WindUnit.KNOTS.value,
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
        central_pressure_hpa=965.0,
        pressure_drop_hpa=35.0,
        imd_category=IMDCategory.VERY_SEVERE_CYCLONIC_STORM.value,
        is_retrospective_best_track=True,
        quality_flag="SYNTHETIC_VERIFIED",
    )
    db_session.add(obs)
    db_session.flush()

    # Query back
    stmt = select(TrackObservation).where(TrackObservation.id == obs_id)
    saved = db_session.execute(stmt).scalar_one()
    assert saved.storm_id == synthetic_storm.id
    assert saved.wind_speed_knots == 75.0
    assert saved.averaging_period == "3-min"
    assert saved.latitude == 16.5
    assert saved.longitude == 87.5


@pytest.mark.integration
def test_duplicate_source_rejection(db_session: Session, synthetic_data_source: DataSource):
    """Verify unique constraint on (provider_name, dataset_name, version)."""
    duplicate = DataSource(
        id=uuid.uuid4(),
        provider_name=synthetic_data_source.provider_name,
        dataset_name=synthetic_data_source.dataset_name,
        version=synthetic_data_source.version,  # Duplicate combination
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


@pytest.mark.integration
def test_invalid_latitude_rejection(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify CheckConstraint rejects latitude > 90.0 degrees."""
    invalid_lat_obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="INVALID-LAT-001",
        observation_time_utc=datetime.now(UTC),
        latitude=95.0,  # Physically impossible latitude
        longitude=85.0,
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
    )
    db_session.add(invalid_lat_obs)
    with pytest.raises((IntegrityError, DBAPIError)):
        db_session.flush()
    db_session.rollback()


@pytest.mark.integration
def test_invalid_longitude_rejection(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify CheckConstraint rejects longitude > 180.0 degrees."""
    invalid_lon_obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="INVALID-LON-001",
        observation_time_utc=datetime.now(UTC),
        latitude=15.0,
        longitude=185.0,  # Physically impossible longitude
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
    )
    db_session.add(invalid_lon_obs)
    with pytest.raises((IntegrityError, DBAPIError)):
        db_session.flush()
    db_session.rollback()


@pytest.mark.integration
def test_null_missing_data_preservation(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify missing meteorological observations remain NULL and are never coerced to 0."""
    obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="NULL-MET-001",
        observation_time_utc=datetime(2024, 5, 20, 12, 0, 0, tzinfo=UTC),
        latitude=17.2,
        longitude=88.1,
        wind_speed_knots=None,  # Missing wind
        central_pressure_hpa=None,  # Missing pressure
        pressure_drop_hpa=None,
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
    )
    db_session.add(obs)
    db_session.flush()

    queried = db_session.get(TrackObservation, obs.id)
    assert queried is not None
    assert queried.wind_speed_knots is None
    assert queried.central_pressure_hpa is None
    assert queried.wind_speed_knots != 0
    assert queried.central_pressure_hpa != 0


@pytest.mark.integration
def test_agency_convention_preservation_coexistence(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify different agencies' reports for same storm and time coexist without collision."""
    obs_time = datetime(2024, 5, 20, 18, 0, 0, tzinfo=UTC)

    # 1. IMD observation (3-minute sustained wind)
    imd_obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="IMD-20240520-18",
        observation_time_utc=obs_time,
        latitude=17.8,
        longitude=88.4,
        wind_speed_knots=85.0,  # 3-min MSW
        averaging_period=AveragingPeriod.THREE_MINUTE.value,
        imd_category=IMDCategory.VERY_SEVERE_CYCLONIC_STORM.value,
    )

    # 2. JTWC observation for same storm and time (1-minute sustained wind)
    jtwc_obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.JTWC.value,
        source_record_id="JTWC-20240520-18",
        observation_time_utc=obs_time,
        latitude=17.9,
        longitude=88.3,
        wind_speed_knots=95.0,  # 1-min MSW (higher than 3-min)
        averaging_period=AveragingPeriod.ONE_MINUTE.value,
    )

    db_session.add(imd_obs)
    db_session.add(jtwc_obs)
    db_session.flush()

    # Query both records
    stmt = (
        select(TrackObservation)
        .where(
            TrackObservation.storm_id == synthetic_storm.id,
            TrackObservation.observation_time_utc == obs_time,
        )
        .order_by(TrackObservation.source_agency)
    )
    records = db_session.execute(stmt).scalars().all()
    assert len(records) == 2

    # Verify separate averaging periods and agency attribution
    agencies = {r.source_agency: r.averaging_period for r in records}
    assert agencies[Agency.IMD.value] == "3-min"
    assert agencies[Agency.JTWC.value] == "1-min"


@pytest.mark.integration
def test_transaction_rollback_guarantee(db_session: Session, synthetic_data_source: DataSource):
    """Verify that an error inside a nested transaction cleanly rolls back without leaking records."""
    initial_count = db_session.query(DataSource).count()

    try:
        with db_session.begin_nested():
            # Trigger deliberate integrity violation using duplicate DataSource
            dup_source = DataSource(
                id=uuid.uuid4(),
                provider_name=synthetic_data_source.provider_name,
                dataset_name=synthetic_data_source.dataset_name,
                version=synthetic_data_source.version,  # Violates uq_datasource_triple
            )
            db_session.add(dup_source)
            db_session.flush()
    except IntegrityError:
        pass  # Expected nested rollback

    after_count = db_session.query(DataSource).count()
    assert after_count == initial_count
