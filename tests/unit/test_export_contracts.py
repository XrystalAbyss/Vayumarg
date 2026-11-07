"""Unit tests for Module A and Module B export contracts."""

import uuid
from datetime import UTC, datetime

from vayumarg.contracts.export import (
    ModuleAExportRecord,
    ModuleBExportRecord,
    ModuleBTrajectoryPoint,
)


def test_module_a_export_contract():
    record = ModuleAExportRecord(
        storm_id=uuid.uuid4(),
        sid="2020136N10088",
        canonical_name="AMPHAN",
        season_year=2020,
        primary_basin="NI",
        observation_time_utc=datetime(2020, 5, 17, 3, 0, tzinfo=UTC),
        latitude=11.3,
        longitude=86.1,
        imd_wind_speed_knots=50.0,
        imd_category="SCS",
        jtwc_wind_speed_knots=65.0,
        wmo_wind_speed_knots=50.0,
        central_pressure_hpa=990.0,
        is_retrospective_best_track=True,
    )

    assert record.sid == "2020136N10088"
    assert record.imd_wind_speed_knots == 50.0
    assert record.jtwc_wind_speed_knots == 65.0
    assert record.is_retrospective_best_track is True
    assert record.satellite_matching_window_minutes == 30


def test_module_b_export_contract():
    point = ModuleBTrajectoryPoint(
        step_index=0,
        observation_time_utc=datetime(2020, 5, 15, 6, 0, tzinfo=UTC),
        latitude=9.5,
        longitude=87.5,
        source_agency="IBTRACS",
        averaging_period="10-min",
        wind_speed_knots=25.0,
        central_pressure_hpa=1000.0,
        is_retrospective_best_track=True,
    )

    record = ModuleBExportRecord(
        storm_id=uuid.uuid4(),
        sid="2020136N10088",
        canonical_name="AMPHAN",
        season_year=2020,
        primary_basin="NI",
        total_trajectory_points=1,
        trajectory=[point],
    )

    assert record.total_trajectory_points == 1
    assert record.trajectory[0].wind_speed_knots == 25.0
    assert record.trajectory[0].is_retrospective_best_track is True
