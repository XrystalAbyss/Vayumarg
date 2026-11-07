"""Initial scientific schema with PostGIS support.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-01 16:30:00.000000

"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 0. Enable PostGIS extension if PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 1. data_sources
    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_name", sa.String(100), nullable=False),
        sa.Column("dataset_name", sa.String(150), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("citation", sa.Text(), nullable=True),
        sa.Column("license", sa.String(100), nullable=True, server_default="Open Access"),
        sa.Column("access_policy", sa.Text(), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "provider_name", "dataset_name", "version", name="uq_datasource_triple"
        ),
    )

    # 2. source_assets
    op.create_table(
        "source_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "data_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("artifact_uri", sa.String(1024), nullable=False),
        sa.Column("sha256_checksum", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("retrieval_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset_metadata", sa.JSON(), nullable=True),
        sa.UniqueConstraint("sha256_checksum", "artifact_uri", name="uq_source_asset_identity"),
    )
    op.create_index("ix_source_assets_sha256", "source_assets", ["sha256_checksum"])

    # 3. ingestion_runs
    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "data_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("started_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="STARTED"),
        sa.Column("records_read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("transaction_outcome", sa.Text(), nullable=True),
    )

    # 4. storms
    op.create_table(
        "storms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_name", sa.String(100), nullable=False),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("primary_basin", sa.String(20), nullable=False),
        sa.Column("nature", sa.String(50), nullable=False, server_default="TS"),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "canonical_name", "season_year", "primary_basin", name="uq_storm_canonical"
        ),
    )
    op.create_index("ix_storms_basin_season", "storms", ["primary_basin", "season_year"])

    # 5. storm_aliases
    op.create_table(
        "storm_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "storm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("storms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_agency", sa.String(50), nullable=False),
        sa.Column("agency_storm_id", sa.String(100), nullable=False),
        sa.Column("agency_storm_name", sa.String(100), nullable=True),
        sa.Column("matching_confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("documented_evidence", sa.Text(), nullable=True),
        sa.UniqueConstraint("source_agency", "agency_storm_id", name="uq_agency_storm_alias"),
        sa.CheckConstraint(
            "matching_confidence >= 0.0 AND matching_confidence <= 1.0",
            name="ck_alias_confidence_range",
        ),
    )

    # 6. track_observations
    op.create_table(
        "track_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "storm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("storms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_agency", sa.String(50), nullable=False),
        sa.Column("source_record_id", sa.String(200), nullable=False),
        sa.Column("observation_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retrieval_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_availability_time_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_retrospective_best_track", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
            nullable=True,
        ),
        sa.Column("wind_speed_knots", sa.Float(), nullable=True),
        sa.Column("original_wind_speed", sa.Float(), nullable=True),
        sa.Column("original_wind_unit", sa.String(20), nullable=True),
        sa.Column("averaging_period", sa.String(20), nullable=False),
        sa.Column("central_pressure_hpa", sa.Float(), nullable=True),
        sa.Column("pressure_drop_hpa", sa.Float(), nullable=True),
        sa.Column("imd_category", sa.String(20), nullable=True),
        sa.Column("quality_flag", sa.String(50), nullable=False, server_default="VALID"),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="ck_track_lat_range"),
        sa.CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="ck_track_lon_range"),
        sa.CheckConstraint(
            "wind_speed_knots IS NULL OR (wind_speed_knots >= 0.0 AND wind_speed_knots <= 300.0)",
            name="ck_track_wind_range",
        ),
        sa.CheckConstraint(
            "central_pressure_hpa IS NULL OR (central_pressure_hpa >= 800.0 AND central_pressure_hpa <= 1080.0)",
            name="ck_track_pressure_range",
        ),
        sa.UniqueConstraint(
            "storm_id",
            "source_agency",
            "observation_time_utc",
            "source_record_id",
            name="uq_storm_agency_obs_record",
        ),
    )
    op.create_index("ix_track_obs_time", "track_observations", ["observation_time_utc"])
    op.create_index(
        "ix_track_storm_time", "track_observations", ["storm_id", "observation_time_utc"]
    )
    op.create_index(
        "ix_track_agency_time", "track_observations", ["source_agency", "observation_time_utc"]
    )

    # 7. data_quality_issues
    op.create_table(
        "data_quality_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "track_observation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("track_observations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("cause", sa.String(255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("resolution_status", sa.String(50), nullable=False, server_default="OPEN"),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
    )

    # 8. dataset_snapshots
    op.create_table(
        "dataset_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_name", sa.String(150), nullable=False),
        sa.Column("transformation_version", sa.String(50), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("total_samples", sa.Integer(), nullable=False),
        sa.Column("filter_criteria", sa.JSON(), nullable=True),
        sa.Column("manifest_uri", sa.String(1024), nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "snapshot_name",
            "transformation_version",
            "manifest_sha256",
            name="uq_snapshot_version_hash",
        ),
    )


def downgrade() -> None:
    op.drop_table("dataset_snapshots")
    op.drop_table("data_quality_issues")
    op.drop_table("track_observations")
    op.drop_table("storm_aliases")
    op.drop_table("storms")
    op.drop_table("ingestion_runs")
    op.drop_table("source_assets")
    op.drop_table("data_sources")
