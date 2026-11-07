"""Integration tests for scientific reconciliation, snapshot freeze, and data quality issues."""

import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency
from vayumarg.database.schema import (
    DataQualityIssue,
    SourceAsset,
    Storm,
    TrackObservation,
)
from vayumarg.quality.reconciliation import execute_scientific_reconciliation
from vayumarg.quality.snapshot import freeze_dataset_snapshot


def test_reconciliation_and_quality_issue_persistence(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify scientific reconciliation updates averaging periods and persists quality issues."""
    now = datetime.now(UTC)

    # 1. IBTRACS with WMO_AGENCY 'newdelhi' (should become 3-min)
    obs_imd = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IBTRACS.value,
        wmo_agency=None,  # to be populated from raw_payload
        source_record_id="OBS_TEST_WMO_NEWDELHI",
        observation_time_utc=now,
        latitude=12.0,
        longitude=85.0,
        wind_speed_knots=45.0,
        averaging_period="10-min",  # wrong F1 initial value
        quality_flag="VALID",
        raw_payload={"wmo_agency": "newdelhi"},
    )

    # 2. IBTRACS with WMO_AGENCY 'tokyo' (should remain 10-min)
    obs_tokyo = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IBTRACS.value,
        wmo_agency=None,
        source_record_id="OBS_TEST_WMO_TOKYO",
        observation_time_utc=now,
        latitude=14.0,
        longitude=86.0,
        wind_speed_knots=50.0,
        averaging_period="10-min",
        quality_flag="VALID",
        raw_payload={"wmo_agency": "tokyo"},
    )

    # 3. IBTRACS with WMO_AGENCY 'hurdat_atl' (should become 1-min)
    obs_nhc = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IBTRACS.value,
        wmo_agency=None,
        source_record_id="OBS_TEST_WMO_HURDAT",
        observation_time_utc=now,
        latitude=15.0,
        longitude=87.0,
        wind_speed_knots=35.0,
        averaging_period="10-min",
        quality_flag="VALID",
        raw_payload={"wmo_agency": "hurdat_atl"},
    )

    # 4. Null wind observation (should become 'unknown')
    obs_null = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id="OBS_TEST_NULL_WIND",
        observation_time_utc=now,
        latitude=16.0,
        longitude=88.0,
        wind_speed_knots=None,
        averaging_period="3-min",
        quality_flag="VALID",
    )

    # 5. Cross-basin observation (latitude > 40N)
    obs_cross = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IBTRACS.value,
        source_record_id="OBS_TEST_CROSS_BASIN",
        observation_time_utc=now,
        latitude=82.5,  # Far Arctic
        longitude=45.0,
        wind_speed_knots=None,
        averaging_period="10-min",
        quality_flag="VALID",
    )

    db_session.add_all([obs_imd, obs_tokyo, obs_nhc, obs_null, obs_cross])
    db_session.flush()

    # Execute reconciliation
    diff = execute_scientific_reconciliation(db_session)
    assert diff is not None

    # Verify updated fields in database
    db_session.refresh(obs_imd)
    assert obs_imd.wmo_agency == "newdelhi"
    assert obs_imd.averaging_period == "3-min"

    db_session.refresh(obs_tokyo)
    assert obs_tokyo.wmo_agency == "tokyo"
    assert obs_tokyo.averaging_period == "10-min"

    db_session.refresh(obs_nhc)
    assert obs_nhc.wmo_agency == "hurdat_atl"
    assert obs_nhc.averaging_period == "1-min"

    db_session.refresh(obs_null)
    assert obs_null.averaging_period == "unknown"

    db_session.refresh(obs_cross)
    assert obs_cross.quality_flag == "CROSS_BASIN"
    assert obs_cross.averaging_period == "unknown"

    # Verify DataQualityIssue entries created
    issues = db_session.execute(select(DataQualityIssue)).scalars().all()
    assert len(issues) >= 3
    causes = {i.cause for i in issues}
    assert "CROSS_BASIN_TRACK_POINTS" in causes


def test_freeze_dataset_snapshot_lifecycle(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify cryptographic snapshot freeze, manifest generation, and idempotency."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest_path = Path(tmp_dir) / "test_freeze_manifest.json"

        # Freeze snapshot
        snapshot1 = freeze_dataset_snapshot(
            session=db_session,
            snapshot_name="test-snapshot-freeze",
            transformation_version="v-test",
            manifest_path=manifest_path,
        )

        assert snapshot1 is not None
        assert snapshot1.id is not None
        assert len(snapshot1.manifest_sha256) == 64
        assert manifest_path.is_file()

        # Re-freezing the identical state is idempotent
        snapshot2 = freeze_dataset_snapshot(
            session=db_session,
            snapshot_name="test-snapshot-freeze",
            transformation_version="v-test",
            manifest_path=manifest_path,
        )

        assert snapshot2.id == snapshot1.id
        assert snapshot2.manifest_sha256 == snapshot1.manifest_sha256
