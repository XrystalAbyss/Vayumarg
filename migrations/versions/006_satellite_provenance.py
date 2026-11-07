"""Satellite provenance verification status and audit segregation.

Revision ID: 006_satellite_provenance
Revises: 005_satellite_data_foundation
Create Date: 2026-11-01 19:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_satellite_provenance"
down_revision: str | None = "005_satellite_data_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add verification_status to satellite_granules
    op.add_column(
        "satellite_granules",
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="PROVENANCE_UNVERIFIED",
        ),
    )

    # 2. Add verification_status to satellite_processed_crops
    op.add_column(
        "satellite_processed_crops",
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="PROVENANCE_UNVERIFIED",
        ),
    )

    # 3. Add verification_status to satellite_track_associations
    op.add_column(
        "satellite_track_associations",
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="PROVENANCE_UNVERIFIED",
        ),
    )

    # 4. Data Migration: Mark pilot synthetic fixtures explicitly
    op.execute(
        """
        UPDATE satellite_granules
        SET verification_status = 'SYNTHETIC_FIXTURE'
        WHERE granule_name LIKE '%PILOT%' OR granule_name LIKE '%tcir%';
        """
    )
    op.execute(
        """
        UPDATE satellite_processed_crops
        SET verification_status = 'SYNTHETIC_FIXTURE'
        WHERE granule_id IN (
            SELECT id FROM satellite_granules WHERE verification_status = 'SYNTHETIC_FIXTURE'
        );
        """
    )
    op.execute(
        """
        UPDATE satellite_track_associations
        SET verification_status = 'SYNTHETIC_FIXTURE'
        WHERE crop_id IN (
            SELECT id FROM satellite_processed_crops WHERE verification_status = 'SYNTHETIC_FIXTURE'
        );
        """
    )


def downgrade() -> None:
    op.drop_column("satellite_track_associations", "verification_status")
    op.drop_column("satellite_processed_crops", "verification_status")
    op.drop_column("satellite_granules", "verification_status")
