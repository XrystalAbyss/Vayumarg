"""WMO agency provenance and data quality tracking.

Revision ID: 004_wmo_agency_and_quality_audit
Revises: 003_ibtracs_multi_agency_lineage
Create Date: 2026-11-01 17:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_wmo_agency_and_quality_audit"
down_revision: str | None = "003_ibtracs_multi_agency_lineage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add wmo_agency column to track_observations to preserve authoritative WMO source center
    op.add_column(
        "track_observations",
        sa.Column("wmo_agency", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_track_wmo_agency",
        "track_observations",
        ["wmo_agency"],
    )


def downgrade() -> None:
    op.drop_index("ix_track_wmo_agency", table_name="track_observations")
    op.drop_column("track_observations", "wmo_agency")
