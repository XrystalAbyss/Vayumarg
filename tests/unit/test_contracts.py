"""Unit tests for typed Pydantic scientific data contracts."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from vayumarg.contracts.enums import (
    Agency,
    AssetType,
    AveragingPeriod,
    IMDCategory,
    WindUnit,
)
from vayumarg.contracts.models import (
    DataSourceContract,
    SourceAssetContract,
    TrackObservationContract,
)


@pytest.mark.unit
def test_valid_data_source_contract():
    """Verify validation of a compliant DataSourceContract."""
    contract = DataSourceContract(
        provider_name="IMD",
        dataset_name="RSMC Best Track",
        version="2024.1",
        citation="India Meteorological Department RSMC New Delhi",
    )
    assert contract.provider_name == "IMD"
    assert contract.license == "Open Access"


@pytest.mark.unit
def test_source_asset_invalid_sha256():
    """Verify that an invalid hexadecimal SHA-256 is strictly rejected."""
    with pytest.raises(ValidationError):
        SourceAssetContract(
            data_source_id=uuid.uuid4(),
            artifact_uri="file:///test.csv",
            sha256_checksum="INVALID_SHORT_HASH",
            file_size_bytes=100,
            asset_type=AssetType.TRACK_CSV,
        )


@pytest.mark.unit
def test_track_observation_contract_coordinate_validation():
    """Verify coordinate physical range boundaries in TrackObservationContract."""
    # Latitude > 90 must fail
    with pytest.raises(ValidationError):
        TrackObservationContract(
            storm_id=uuid.uuid4(),
            source_asset_id=uuid.uuid4(),
            source_agency=Agency.IMD,
            source_record_id="REC-001",
            observation_time_utc=datetime.now(UTC),
            latitude=95.5,  # Invalid
            longitude=88.0,
            averaging_period=AveragingPeriod.THREE_MINUTE,
        )

    # Longitude < -180 must fail
    with pytest.raises(ValidationError):
        TrackObservationContract(
            storm_id=uuid.uuid4(),
            source_asset_id=uuid.uuid4(),
            source_agency=Agency.IMD,
            source_record_id="REC-002",
            observation_time_utc=datetime.now(UTC),
            latitude=15.0,
            longitude=-185.0,  # Invalid
            averaging_period=AveragingPeriod.THREE_MINUTE,
        )


@pytest.mark.unit
def test_track_observation_utc_coercion():
    """Verify naive datetimes are converted or enforced to explicit UTC."""
    obs = TrackObservationContract(
        storm_id=uuid.uuid4(),
        source_asset_id=uuid.uuid4(),
        source_agency=Agency.IMD,
        source_record_id="REC-003",
        observation_time_utc=datetime(2024, 5, 20, 12, 0, 0),  # Naive
        latitude=18.5,
        longitude=86.2,
        averaging_period=AveragingPeriod.THREE_MINUTE,
        wind_speed_knots=65.0,
        original_wind_speed=65.0,
        original_wind_unit=WindUnit.KNOTS,
        imd_category=IMDCategory.VERY_SEVERE_CYCLONIC_STORM,
    )
    assert obs.observation_time_utc.tzinfo is not None
    assert obs.observation_time_utc.tzinfo == UTC
