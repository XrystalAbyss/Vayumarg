"""Typed Pydantic data contracts for Vayumarg.

Defines the canonical, strictly-validated data structures shared across
ingestion, quality verification, database persistence, and scientific modules.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vayumarg.contracts.enums import (
    Agency,
    AssetType,
    AveragingPeriod,
    Basin,
    IMDCategory,
    IssueSeverity,
    ResolutionStatus,
    RunStatus,
    WindUnit,
)


class BaseContract(BaseModel):
    """Base Pydantic configuration for all contracts."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class DataSourceContract(BaseContract):
    """Data source registry contract."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider_name: str = Field(..., max_length=100)
    dataset_name: str = Field(..., max_length=150)
    version: str = Field(..., max_length=50)
    citation: str | None = None
    license: str | None = Field(default="Open Access", max_length=100)
    access_policy: str | None = None
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SourceAssetContract(BaseContract):
    """Immutable physical or remote asset record."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    data_source_id: uuid.UUID
    artifact_uri: str = Field(..., max_length=1024)
    sha256_checksum: str = Field(..., min_length=64, max_length=64)
    file_size_bytes: int = Field(..., ge=0)
    asset_type: AssetType
    retrieval_time_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sha256_checksum")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        if not all(c in "0123456789abcdefABCDEF" for c in v):
            raise ValueError("sha256_checksum must be a valid 64-character hexadecimal string")
        return v.lower()


class IngestionRunContract(BaseContract):
    """Ingestion run tracking record."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    data_source_id: uuid.UUID
    source_asset_id: uuid.UUID | None = None
    started_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at_utc: datetime | None = None
    status: RunStatus = RunStatus.STARTED
    records_read: int = Field(default=0, ge=0)
    records_inserted: int = Field(default=0, ge=0)
    records_rejected: int = Field(default=0, ge=0)
    error_details: str | None = None
    transaction_outcome: str | None = None


class StormContract(BaseContract):
    """Canonical storm definition."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    canonical_name: str = Field(..., max_length=100)
    season_year: int = Field(..., ge=1800, le=2100)
    primary_basin: Basin
    nature: str = Field(default="TS", max_length=50)  # e.g. Tropical, Subtropical, Extratropical
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StormAliasContract(BaseContract):
    """Agency-specific storm identifier and naming alias."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    storm_id: uuid.UUID
    source_agency: Agency
    agency_storm_id: str = Field(..., max_length=100)
    agency_storm_name: str | None = Field(default=None, max_length=100)
    matching_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    documented_evidence: str | None = None


class TrackObservationContract(BaseContract):
    """Rigorous scientific cyclone track and intensity observation record."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    storm_id: uuid.UUID
    source_asset_id: uuid.UUID
    source_agency: Agency
    source_record_id: str = Field(..., max_length=200)

    # Temporal Conventions (Explicit UTC)
    observation_time_utc: datetime
    retrieval_time_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_availability_time_utc: datetime | None = None
    is_retrospective_best_track: bool = False
    is_superseded: bool = False

    # Geospatial Coordinates (SRID 4326)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    # Meteorological Observations (Strict null handling: missing is None, never 0)
    wind_speed_knots: float | None = Field(default=None, ge=0.0, le=300.0)
    original_wind_speed: float | None = Field(default=None, ge=0.0)
    original_wind_unit: WindUnit | None = None
    averaging_period: AveragingPeriod = AveragingPeriod.UNKNOWN
    central_pressure_hpa: float | None = Field(default=None, ge=800.0, le=1080.0)
    pressure_drop_hpa: float | None = Field(default=None, ge=0.0, le=200.0)
    imd_category: IMDCategory | None = None

    # Quality & Lineage
    quality_flag: str = Field(default="VALID", max_length=50)
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observation_time_utc", "retrieval_time_utc", "data_availability_time_utc")
    @classmethod
    def ensure_utc(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v


class DataQualityIssueContract(BaseContract):
    """Record-level data quality issue log."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_asset_id: uuid.UUID | None = None
    track_observation_id: uuid.UUID | None = None
    severity: IssueSeverity
    cause: str = Field(..., max_length=255)
    details: dict[str, Any] = Field(default_factory=dict)
    resolution_status: ResolutionStatus = ResolutionStatus.OPEN
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DatasetSnapshotContract(BaseContract):
    """Stable cryptographic snapshot of a transformation or training set."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    snapshot_name: str = Field(..., max_length=150)
    transformation_version: str = Field(..., max_length=50)
    manifest_sha256: str = Field(..., min_length=64, max_length=64)
    total_samples: int = Field(..., ge=0)
    filter_criteria: dict[str, Any] = Field(default_factory=dict)
    manifest_uri: str = Field(..., max_length=1024)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
