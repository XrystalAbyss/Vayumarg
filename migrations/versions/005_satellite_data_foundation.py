"""Satellite data foundation, granules, crops, and track associations.

Revision ID: 005_satellite_data_foundation
Revises: 004_wmo_agency_and_quality_audit
Create Date: 2026-11-01 18:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "005_satellite_data_foundation"
down_revision: str | None = "004_wmo_agency_and_quality_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Satellite Products Registry
    op.create_table(
        "satellite_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("satellite_name", sa.String(length=100), nullable=False),
        sa.Column("sensor_name", sa.String(length=100), nullable=False),
        sa.Column("processing_level", sa.String(length=20), nullable=False),
        sa.Column("spatial_resolution_km", sa.Float(), nullable=False),
        sa.Column("spectral_channels", sa.JSON(), nullable=False),
        sa.Column("calibration_info", sa.JSON(), nullable=True),
        sa.Column(
            "created_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # 2. Satellite Granules (Raw / Primary Scenes)
    op.create_table(
        "satellite_granules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("satellite_products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("granule_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("acquisition_start_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acquisition_end_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_format", sa.String(length=20), nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("granule_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_satellite_granule_acq_start",
        "satellite_granules",
        ["acquisition_start_utc"],
    )
    op.create_index(
        "ix_satellite_granule_sha256",
        "satellite_granules",
        ["sha256_checksum"],
    )

    # 3. Satellite Processed Crops
    op.create_table(
        "satellite_processed_crops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "granule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("satellite_granules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "storm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("storms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("crop_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("center_latitude", sa.Float(), nullable=False),
        sa.Column("center_longitude", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
            nullable=True,
        ),
        sa.Column("pixel_height", sa.Integer(), nullable=False),
        sa.Column("pixel_width", sa.Integer(), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("spatial_resolution_km", sa.Float(), nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
        sa.Column("quality_control_flags", sa.JSON(), nullable=True),
        sa.Column(
            "created_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_satellite_crop_time",
        "satellite_processed_crops",
        ["crop_time_utc"],
    )

    # 4. Satellite Track Associations
    op.create_table(
        "satellite_track_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "crop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("satellite_processed_crops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "track_observation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("track_observations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("temporal_offset_minutes", sa.Float(), nullable=False),
        sa.Column("spatial_offset_km", sa.Float(), nullable=False),
        sa.Column("association_confidence", sa.Float(), nullable=False),
        sa.Column(
            "validation_status", sa.String(length=50), nullable=False, server_default="VALIDATED"
        ),
        sa.Column("is_interpolated_track", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "crop_id", "track_observation_id", name="uq_crop_observation_association"
        ),
    )


def downgrade() -> None:
    op.drop_table("satellite_track_associations")
    op.drop_table("satellite_processed_crops")
    op.drop_table("satellite_granules")
    op.drop_table("satellite_products")
