"""Unit tests for scientific quality validation and conventions."""

import uuid
from datetime import UTC, datetime

import pytest

from vayumarg.contracts.enums import Agency, AveragingPeriod
from vayumarg.quality.validator import (
    validate_agency_averaging_period,
    validate_coordinates,
    validate_observation_record,
)


@pytest.mark.unit
def test_coordinate_validator():
    """Verify physical coordinate range validation."""
    valid, _ = validate_coordinates(20.5, 88.2)
    assert valid is True

    invalid_lat, err = validate_coordinates(91.0, 88.2)
    assert invalid_lat is False
    assert "Latitude" in err

    invalid_lon, err = validate_coordinates(20.5, 185.0)
    assert invalid_lon is False
    assert "Longitude" in err


@pytest.mark.unit
def test_agency_averaging_convention_validation():
    """Verify detection of mismatched sustained wind averaging periods."""
    # IMD must be 3-min
    valid_imd, _ = validate_agency_averaging_period(Agency.IMD, AveragingPeriod.THREE_MINUTE)
    assert valid_imd is True

    # IMD reported as 1-min must be flagged as mismatch
    invalid_imd, err = validate_agency_averaging_period(Agency.IMD, AveragingPeriod.ONE_MINUTE)
    assert invalid_imd is False
    assert "IMD standard requires 3-minute sustained wind" in err

    # JTWC must be 1-min
    valid_jtwc, _ = validate_agency_averaging_period(Agency.JTWC, AveragingPeriod.ONE_MINUTE)
    assert valid_jtwc is True


@pytest.mark.unit
def test_suspicious_zero_wind_speed_detection():
    """Verify that zero wind speed with deep central pressure is flagged as suspicious."""
    rec = {
        "storm_id": uuid.uuid4(),
        "source_asset_id": uuid.uuid4(),
        "source_agency": Agency.IMD.value,
        "source_record_id": "SYNTH-001",
        "observation_time_utc": datetime.now(UTC),
        "latitude": 14.5,
        "longitude": 84.0,
        "wind_speed_knots": 0.0,  # Suspicious 0 instead of null
        "central_pressure_hpa": 940.0,
        "averaging_period": AveragingPeriod.THREE_MINUTE.value,
    }
    valid, errors = validate_observation_record(rec)
    assert valid is False
    assert any("Suspicious zero wind speed" in e for e in errors)
