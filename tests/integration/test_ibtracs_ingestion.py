"""Integration tests for authoritative NOAA IBTrACS ingestion."""

from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency
from vayumarg.database.schema import (
    DataSource,
    SourceAsset,
    Storm,
    StormAlias,
    TrackObservation,
)
from vayumarg.ingestion.ibtracs_ingest import run_ibtracs_ingestion


@pytest.mark.integration
def test_ibtracs_pilot_ingestion_and_idempotency(db_session: Session):
    """Verify pilot ingestion of benchmark cyclones (AMPHAN, BIPARJOY) and verify idempotency."""
    raw_csv = Path("data/raw/ibtracs_ni_v04r01.csv")
    if not raw_csv.is_file():
        pytest.skip("Raw IBTrACS file not available on local disk for integration test")

    # 1. Execute initial pilot ingestion
    run1 = run_ibtracs_ingestion(
        pilot=True,
        file_path=raw_csv,
        session_override=db_session,
        batch_size=500,
    )

    assert run1.status == "COMPLETED"
    assert run1.records_read == 164  # 51 AMPHAN rows + 113 BIPARJOY rows
    assert run1.records_inserted > 0
    assert run1.records_rejected == 0

    # 2. Verify DataSource
    ds = db_session.execute(
        select(DataSource).where(DataSource.provider_name == "NOAA NCEI")
    ).scalar_one()
    assert ds.version == "v04r01"

    # 3. Verify SourceAsset
    asset = db_session.execute(
        select(SourceAsset).where(SourceAsset.data_source_id == ds.id)
    ).scalar_one()
    assert asset.asset_type == "RAW_CSV"
    assert asset.file_size_bytes == 27895917

    # 4. Verify Storms
    storms = db_session.execute(select(Storm)).scalars().all()
    storm_names = {s.canonical_name for s in storms}
    assert "AMPHAN" in storm_names
    assert "BIPARJOY" in storm_names

    # 5. Verify StormAliases
    aliases = db_session.execute(select(StormAlias)).scalars().all()
    agency_set = {a.source_agency for a in aliases}
    assert Agency.IBTRACS.value in agency_set
    assert Agency.JTWC.value in agency_set

    # Check AMPHAN SID
    amphan_alias = db_session.execute(
        select(StormAlias).where(StormAlias.agency_storm_id == "2020136N10088")
    ).scalar_one()
    assert amphan_alias.agency_storm_name == "AMPHAN"

    # 6. Verify Track Observations
    obs_count = db_session.execute(select(func.count(TrackObservation.id))).scalar_one()
    assert obs_count == run1.records_inserted

    # Verify Multi-agency observations co-exist for AMPHAN
    amphan_storm = db_session.execute(
        select(Storm).where(Storm.canonical_name == "AMPHAN")
    ).scalar_one()

    amphan_agencies = set(
        db_session.execute(
            select(TrackObservation.source_agency).where(
                TrackObservation.storm_id == amphan_storm.id
            )
        )
        .scalars()
        .all()
    )
    assert Agency.IBTRACS.value in amphan_agencies
    assert Agency.IMD.value in amphan_agencies
    assert Agency.JTWC.value in amphan_agencies

    # Verify PostGIS geometry
    sample_obs = (
        db_session.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == amphan_storm.id,
                TrackObservation.geom.is_not(None),
            )
        )
        .scalars()
        .first()
    )
    assert sample_obs is not None

    geom_text = db_session.execute(
        select(func.ST_AsText(TrackObservation.geom)).where(TrackObservation.id == sample_obs.id)
    ).scalar_one()
    assert geom_text.startswith("POINT(")

    # 7. Test Idempotency: Re-run pilot ingestion and ensure 0 duplicate errors and 0 new inserts
    run2 = run_ibtracs_ingestion(
        pilot=True,
        file_path=raw_csv,
        session_override=db_session,
        batch_size=500,
    )
    assert run2.status == "COMPLETED"
    assert run2.records_read == 164
    assert run2.records_inserted == 0  # No duplicate insertions
    assert run2.records_rejected == obs_count  # All existing observations skipped
