"""SQLAlchemy 2 database schema definitions for Vayumarg.

Defines the relational and geospatial foundation adhering to WMO/IMD scientific standards,
explicit UTC temporal tracking, PostGIS SRID 4326 geometries, and strict physical constraints.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative model."""

    pass


class DataSource(Base):
    """Data source registry entity."""

    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(150), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True, default="Open Access")
    access_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    assets: Mapped[list["SourceAsset"]] = relationship(
        "SourceAsset", back_populates="data_source", cascade="all, delete-orphan"
    )
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun", back_populates="data_source"
    )

    __table_args__ = (
        UniqueConstraint("provider_name", "dataset_name", "version", name="uq_datasource_triple"),
    )


class SourceAsset(Base):
    """Immutable physical or remote data asset tracked via SHA-256."""

    __tablename__ = "source_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    artifact_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    retrieval_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    asset_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    data_source: Mapped["DataSource"] = relationship("DataSource", back_populates="assets")
    observations: Mapped[list["TrackObservation"]] = relationship(
        "TrackObservation", back_populates="source_asset"
    )
    quality_issues: Mapped[list["DataQualityIssue"]] = relationship(
        "DataQualityIssue", back_populates="source_asset"
    )

    __table_args__ = (
        UniqueConstraint("sha256_checksum", "artifact_uri", name="uq_source_asset_identity"),
    )


class IngestionRun(Base):
    """Audit log of ingestion execution and outcome."""

    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="STARTED")
    records_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    data_source: Mapped["DataSource"] = relationship("DataSource", back_populates="ingestion_runs")


class Storm(Base):
    """Canonical cyclone event entity."""

    __tablename__ = "storms"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    canonical_name: Mapped[str] = mapped_column(String(100), nullable=False)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_basin: Mapped[str] = mapped_column(String(20), nullable=False)
    nature: Mapped[str] = mapped_column(String(50), nullable=False, default="TS")
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    aliases: Mapped[list["StormAlias"]] = relationship(
        "StormAlias", back_populates="storm", cascade="all, delete-orphan"
    )
    observations: Mapped[list["TrackObservation"]] = relationship(
        "TrackObservation", back_populates="storm", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_storms_basin_season", "primary_basin", "season_year"),)


class StormAlias(Base):
    """Cross-agency storm identification alias."""

    __tablename__ = "storm_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    storm_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("storms.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_agency: Mapped[str] = mapped_column(String(50), nullable=False)
    agency_storm_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agency_storm_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    matching_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    documented_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    storm: Mapped["Storm"] = relationship("Storm", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("source_agency", "agency_storm_id", name="uq_agency_storm_alias"),
        CheckConstraint(
            "matching_confidence >= 0.0 AND matching_confidence <= 1.0",
            name="ck_alias_confidence_range",
        ),
    )


class TrackObservation(Base):
    """Geospatial cyclone track and intensity observation."""

    __tablename__ = "track_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    storm_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("storms.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_asset_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_agency: Mapped[str] = mapped_column(String(50), nullable=False)
    wmo_agency: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    source_record_id: Mapped[str] = mapped_column(String(200), nullable=False)

    # Temporal Conventions
    observation_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    retrieval_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    data_availability_time_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_retrospective_best_track: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_superseded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Geospatial Coordinates (SRID 4326)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # Meteorological Fields
    wind_speed_knots: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_wind_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    averaging_period: Mapped[str] = mapped_column(String(20), nullable=False)
    central_pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_drop_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    imd_category: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Quality & Lineage
    quality_flag: Mapped[str] = mapped_column(String(50), nullable=False, default="VALID")
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    storm: Mapped["Storm"] = relationship("Storm", back_populates="observations")
    source_asset: Mapped["SourceAsset"] = relationship("SourceAsset", back_populates="observations")
    quality_issues: Mapped[list["DataQualityIssue"]] = relationship(
        "DataQualityIssue", back_populates="track_observation"
    )

    __table_args__ = (
        CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="ck_track_lat_range"),
        CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="ck_track_lon_range"),
        CheckConstraint(
            "wind_speed_knots IS NULL OR (wind_speed_knots >= 0.0 AND wind_speed_knots <= 300.0)",
            name="ck_track_wind_range",
        ),
        CheckConstraint(
            "central_pressure_hpa IS NULL OR (central_pressure_hpa >= 800.0 AND central_pressure_hpa <= 1080.0)",
            name="ck_track_pressure_range",
        ),
        UniqueConstraint(
            "source_asset_id",
            "source_record_id",
            "source_agency",
            name="uq_track_asset_record_agency",
        ),
        UniqueConstraint(
            "storm_id",
            "source_agency",
            "source_asset_id",
            "observation_time_utc",
            "source_record_id",
            name="uq_storm_agency_asset_obs_record",
        ),
        Index("ix_track_storm_time", "storm_id", "observation_time_utc"),
        Index("ix_track_agency_time", "source_agency", "observation_time_utc"),
    )


class DataQualityIssue(Base):
    """Quality issue log associated with records or assets."""

    __tablename__ = "data_quality_issues"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    track_observation_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("track_observations.id", ondelete="CASCADE"),
        nullable=True,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    cause: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN")
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    source_asset: Mapped["SourceAsset | None"] = relationship(
        "SourceAsset", back_populates="quality_issues"
    )
    track_observation: Mapped["TrackObservation | None"] = relationship(
        "TrackObservation", back_populates="quality_issues"
    )


class DatasetSnapshot(Base):
    """Manifest snapshot tracking reproducible dataset splits and transformations."""

    __tablename__ = "dataset_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_name: Mapped[str] = mapped_column(String(150), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    filter_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    manifest_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "snapshot_name",
            "transformation_version",
            "manifest_sha256",
            name="uq_snapshot_version_hash",
        ),
    )


class SatelliteProduct(Base):
    """Satellite mission and instrument product registry."""

    __tablename__ = "satellite_products"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    satellite_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sensor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    processing_level: Mapped[str] = mapped_column(String(20), nullable=False)
    spatial_resolution_km: Mapped[float] = mapped_column(Float, nullable=False)
    spectral_channels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    calibration_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    granules: Mapped[list["SatelliteGranule"]] = relationship(
        "SatelliteGranule", back_populates="product"
    )


class SatelliteGranule(Base):
    """Raw or primary satellite scene/granule asset tracked on filesystem."""

    __tablename__ = "satellite_granules"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("satellite_products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    granule_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    acquisition_start_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    acquisition_end_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    granule_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PROVENANCE_UNVERIFIED"
    )
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    product: Mapped["SatelliteProduct"] = relationship(
        "SatelliteProduct", back_populates="granules"
    )
    crops: Mapped[list["SatelliteProcessedCrop"]] = relationship(
        "SatelliteProcessedCrop", back_populates="granule"
    )


class SatelliteProcessedCrop(Base):
    """Cyclone-centered preprocessed multi-spectral image patch."""

    __tablename__ = "satellite_processed_crops"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    granule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("satellite_granules.id", ondelete="CASCADE"),
        nullable=False,
    )
    storm_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("storms.id", ondelete="CASCADE"),
        nullable=False,
    )
    crop_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    center_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    center_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    pixel_height: Mapped[int] = mapped_column(Integer, nullable=False)
    pixel_width: Mapped[int] = mapped_column(Integer, nullable=False)
    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    spatial_resolution_km: Mapped[float] = mapped_column(Float, nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    quality_control_flags: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PROVENANCE_UNVERIFIED"
    )
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    granule: Mapped["SatelliteGranule"] = relationship("SatelliteGranule", back_populates="crops")
    storm: Mapped["Storm"] = relationship("Storm")
    associations: Mapped[list["SatelliteTrackAssociation"]] = relationship(
        "SatelliteTrackAssociation", back_populates="crop"
    )


class SatelliteTrackAssociation(Base):
    """Spatiotemporal alignment between satellite crop and ground-truth best-track observation."""

    __tablename__ = "satellite_track_associations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("satellite_processed_crops.id", ondelete="CASCADE"),
        nullable=False,
    )
    track_observation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("track_observations.id", ondelete="CASCADE"),
        nullable=False,
    )
    temporal_offset_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    spatial_offset_km: Mapped[float] = mapped_column(Float, nullable=False)
    association_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="VALIDATED")
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PROVENANCE_UNVERIFIED"
    )
    is_interpolated_track: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    crop: Mapped["SatelliteProcessedCrop"] = relationship(
        "SatelliteProcessedCrop", back_populates="associations"
    )
    track_observation: Mapped["TrackObservation"] = relationship("TrackObservation")

    __table_args__ = (
        UniqueConstraint("crop_id", "track_observation_id", name="uq_crop_observation_association"),
    )
