"""Storm identity and observation revision hardening.

Revision ID: 002_storm_identity_and_safety
Revises: 001_initial_schema
Create Date: 2026-11-01 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_storm_identity_and_safety"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Drop the restrictive storm canonical uniqueness constraint
    # Allows multiple unnamed storms in same season/basin and duplicate storm names across distinct events
    op.drop_constraint("uq_storm_canonical", "storms", type_="unique")

    # 2. Add is_superseded flag to track_observations for immutable revision handling
    op.add_column(
        "track_observations",
        sa.Column("is_superseded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # 3. Drop legacy observation constraint
    op.drop_constraint("uq_storm_agency_obs_record", "track_observations", type_="unique")

    # 4. Add deterministic source-asset scoped uniqueness to prevent duplicate row ingestion
    op.create_unique_constraint(
        "uq_track_asset_record",
        "track_observations",
        ["source_asset_id", "source_record_id"],
    )

    # 5. Add composite storm-agency-asset-observation uniqueness
    op.create_unique_constraint(
        "uq_storm_agency_asset_obs_record",
        "track_observations",
        [
            "storm_id",
            "source_agency",
            "source_asset_id",
            "observation_time_utc",
            "source_record_id",
        ],
    )


def downgrade() -> None:
    op.drop_constraint("uq_storm_agency_asset_obs_record", "track_observations", type_="unique")
    op.drop_constraint("uq_track_asset_record", "track_observations", type_="unique")
    op.create_unique_constraint(
        "uq_storm_agency_obs_record",
        "track_observations",
        ["storm_id", "source_agency", "observation_time_utc", "source_record_id"],
    )
    op.drop_column("track_observations", "is_superseded")
    op.create_unique_constraint(
        "uq_storm_canonical",
        "storms",
        ["canonical_name", "season_year", "primary_basin"],
    )
