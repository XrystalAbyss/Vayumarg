"""Multi-agency observation lineage and row identity refinement.

Revision ID: 003_ibtracs_multi_agency_lineage
Revises: 002_storm_identity_and_safety
Create Date: 2026-11-01 17:15:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "003_ibtracs_multi_agency_lineage"
down_revision: str | None = "002_storm_identity_and_safety"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop single-agency source-asset row constraint
    op.drop_constraint("uq_track_asset_record", "track_observations", type_="unique")

    # Add agency-aware source-asset row constraint allowing multi-agency co-existence per CSV row
    op.create_unique_constraint(
        "uq_track_asset_record_agency",
        "track_observations",
        ["source_asset_id", "source_record_id", "source_agency"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_track_asset_record_agency", "track_observations", type_="unique")
    op.create_unique_constraint(
        "uq_track_asset_record",
        "track_observations",
        ["source_asset_id", "source_record_id"],
    )
