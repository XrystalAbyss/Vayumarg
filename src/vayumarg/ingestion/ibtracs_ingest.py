"""Authoritative NOAA IBTrACS North Indian Ocean Ingestion Engine.

Executes atomic, transactional ingestion of IBTrACS v04r01 data into PostgreSQL/PostGIS:
1. Establishes immutable DataSource and SourceAsset lineage.
2. Resolves and deduplicates canonical Storm and multi-agency StormAlias records.
3. Preserves multi-agency TrackObservation records (IBTrACS, IMD/NEWDELHI, JTWC/USA).
4. Strictly segregates wind averaging conventions (10-min, 3-min, 1-min).
5. Executes inside audit-logged IngestionRun transactions with rollback guarantees.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency
from vayumarg.core.logging import get_logger
from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import (
    DataSource,
    IngestionRun,
    SourceAsset,
    Storm,
    StormAlias,
    TrackObservation,
)
from vayumarg.ingestion.downloader import (
    download_official_ibtracs_ni,
)
from vayumarg.ingestion.ibtracs_parser import IBTrACSParser
from vayumarg.ingestion.transaction import execute_ingestion_transaction

logger = get_logger("vayumarg.ingestion.ibtracs_ingest")

NOAA_PROVIDER_NAME = "NOAA NCEI"
IBTRACS_DATASET_NAME = "IBTrACS North Indian Ocean"
IBTRACS_VERSION = "v04r01"
IBTRACS_CITATION = (
    "Knapp, K. R., et al. (2018). International Best Track Archive for Climate Stewardship "
    "(IBTrACS) Project, Version 4. NOAA National Centers for Environmental Information. "
    "https://doi.org/10.25921/82ty-9e16"
)

# Standard Pilot Benchmarks
PILOT_STORMS = {
    "2020136N10088": "AMPHAN",  # Super Cyclonic Storm Amphan (May 2020)
    "2023156N10067": "BIPARJOY",  # Extremely Severe Cyclonic Storm Biparjoy (June 2023)
}


def get_or_create_data_source(session: Session) -> DataSource:
    """Retrieve or register the canonical NOAA IBTrACS DataSource entity."""
    stmt = select(DataSource).where(
        DataSource.provider_name == NOAA_PROVIDER_NAME,
        DataSource.dataset_name == IBTRACS_DATASET_NAME,
        DataSource.version == IBTRACS_VERSION,
    )
    ds = session.execute(stmt).scalar_one_or_none()
    if ds is None:
        ds = DataSource(
            id=uuid.uuid4(),
            provider_name=NOAA_PROVIDER_NAME,
            dataset_name=IBTRACS_DATASET_NAME,
            version=IBTRACS_VERSION,
            citation=IBTRACS_CITATION,
            license="Open Access / Public Domain",
            access_policy="Unrestricted scientific research access",
            created_at_utc=datetime.now(UTC),
        )
        session.add(ds)
        session.flush()
        logger.info("Registered DataSource: %s %s (%s)", ds.provider_name, ds.dataset_name, ds.id)
    return ds


def get_or_create_source_asset(
    session: Session,
    data_source_id: uuid.UUID,
    file_path: Path,
    manifest: dict[str, Any],
) -> SourceAsset:
    """Retrieve or create the immutable SourceAsset record for the raw CSV."""
    sha256 = manifest["sha256"]
    artifact_uri = f"file:///{file_path.resolve().as_posix()}"

    stmt = select(SourceAsset).where(
        SourceAsset.sha256_checksum == sha256,
        SourceAsset.artifact_uri == artifact_uri,
    )
    asset = session.execute(stmt).scalar_one_or_none()
    if asset is None:
        asset = SourceAsset(
            id=uuid.uuid4(),
            data_source_id=data_source_id,
            artifact_uri=artifact_uri,
            sha256_checksum=sha256,
            file_size_bytes=manifest["size_bytes"],
            asset_type="RAW_CSV",
            retrieval_time_utc=datetime.now(UTC),
            asset_metadata=manifest.get("metadata", {}),
        )
        session.add(asset)
        session.flush()
        logger.info("Registered SourceAsset: %s (%s)", asset.artifact_uri, asset.id)
    return asset


def ingest_ibtracs_data(
    session: Session,
    source_asset: SourceAsset,
    file_path: Path,
    sid_filter: set[str] | None = None,
    batch_size: int = 5000,
) -> tuple[int, int, int]:
    """Execute streaming parsing and transactional batch insertion of IBTrACS records.

    Optimized two-pass architecture:
    Pass 1: Collect and bulk-insert all distinct storms and aliases.
    Pass 2: Stream and bulk-insert observations in batches with session expunge.

    Returns:
        (records_read, records_inserted, records_rejected)
    """
    parser = IBTrACSParser(file_path)

    # 1. Pre-cache existing storm SIDs mapped to storm_id
    existing_aliases = session.execute(
        select(StormAlias.agency_storm_id, StormAlias.storm_id).where(
            StormAlias.source_agency == Agency.IBTRACS.value
        )
    ).all()
    sid_to_storm_id: dict[str, uuid.UUID] = {row[0]: row[1] for row in existing_aliases}

    # 2. Pass 1: Discover all distinct storms in the target dataset
    logger.info("Pass 1: Scanning storms and building canonical registry...")
    storms_to_create: dict[str, dict[str, Any]] = {}
    for storm_info, _ in parser.iter_records(sid_filter=sid_filter):
        sid = storm_info["sid"]
        if sid not in sid_to_storm_id and sid not in storms_to_create:
            storms_to_create[sid] = storm_info

    if storms_to_create:
        logger.info("Registering %d new storms and aliases...", len(storms_to_create))
        for sid, s_info in storms_to_create.items():
            new_storm_id = uuid.uuid4()
            new_storm = Storm(
                id=new_storm_id,
                canonical_name=s_info["canonical_name"],
                season_year=s_info["season_year"],
                primary_basin=s_info["primary_basin"],
                nature=s_info["nature"],
                created_at_utc=datetime.now(UTC),
            )
            session.add(new_storm)
            sid_to_storm_id[sid] = new_storm_id

            # Primary IBTrACS Alias
            ibtracs_alias = StormAlias(
                id=uuid.uuid4(),
                storm_id=new_storm_id,
                source_agency=Agency.IBTRACS.value,
                agency_storm_id=sid,
                agency_storm_name=s_info["raw_name"],
                matching_confidence=1.0,
                documented_evidence="NOAA IBTrACS v04r01 authoritative storm SID",
            )
            session.add(ibtracs_alias)

            # Optional JTWC ATCF Alias if available
            if s_info.get("usa_atcf_id"):
                jtwc_alias = StormAlias(
                    id=uuid.uuid4(),
                    storm_id=new_storm_id,
                    source_agency=Agency.JTWC.value,
                    agency_storm_id=s_info["usa_atcf_id"],
                    agency_storm_name=s_info["raw_name"],
                    matching_confidence=1.0,
                    documented_evidence="NOAA IBTrACS USA_ATCF_ID cross-reference",
                )
                session.add(jtwc_alias)

        session.flush()
        session.expunge_all()
        logger.info("Canonical storms and aliases successfully registered.")

    # 3. Pre-cache existing observation keys for this source asset
    existing_obs_keys = set(
        session.execute(
            select(TrackObservation.source_record_id, TrackObservation.source_agency).where(
                TrackObservation.source_asset_id == source_asset.id
            )
        ).all()
    )

    # 4. Pass 2: Stream and bulk-insert track observations
    logger.info("Pass 2: Streaming track observations (batch size: %d)...", batch_size)
    records_read = 0
    records_inserted = 0
    records_rejected = 0
    observation_batch: list[TrackObservation] = []

    for storm_info, obs_list in parser.iter_records(sid_filter=sid_filter):
        records_read += 1
        sid = storm_info["sid"]
        storm_id = sid_to_storm_id[sid]

        for obs_data in obs_list:
            key = (obs_data["source_record_id"], obs_data["source_agency"])
            if key in existing_obs_keys:
                records_rejected += 1
                continue

            obs = TrackObservation(
                id=uuid.uuid4(),
                storm_id=storm_id,
                source_asset_id=source_asset.id,
                source_agency=obs_data["source_agency"],
                wmo_agency=obs_data.get("wmo_agency"),
                source_record_id=obs_data["source_record_id"],
                observation_time_utc=obs_data["observation_time_utc"],
                retrieval_time_utc=datetime.now(UTC),
                is_retrospective_best_track=obs_data["is_retrospective_best_track"],
                latitude=obs_data["latitude"],
                longitude=obs_data["longitude"],
                geom=obs_data["geom"],
                wind_speed_knots=obs_data["wind_speed_knots"],
                original_wind_speed=obs_data["original_wind_speed"],
                original_wind_unit=obs_data["original_wind_unit"],
                averaging_period=obs_data["averaging_period"],
                central_pressure_hpa=obs_data["central_pressure_hpa"],
                pressure_drop_hpa=obs_data["pressure_drop_hpa"],
                imd_category=obs_data["imd_category"],
                quality_flag=obs_data["quality_flag"],
                raw_payload=obs_data["raw_payload"],
            )
            observation_batch.append(obs)
            existing_obs_keys.add(key)
            records_inserted += 1

            if len(observation_batch) >= batch_size:
                session.add_all(observation_batch)
                session.flush()
                session.expunge_all()
                observation_batch.clear()

        if records_read % 10000 == 0:
            logger.info(
                "Ingestion progress: %d raw rows processed, %d observations inserted",
                records_read,
                records_inserted,
            )

    if observation_batch:
        session.add_all(observation_batch)
        session.flush()
        session.expunge_all()
        observation_batch.clear()

    logger.info(
        "Ingestion completed: %d raw rows read, %d observations inserted, %d rejected/skipped",
        records_read,
        records_inserted,
        records_rejected,
    )
    return records_read, records_inserted, records_rejected


def run_ibtracs_ingestion(
    pilot: bool = False,
    file_path: Path | None = None,
    session_override: Session | None = None,
    batch_size: int = 5000,
) -> IngestionRun:
    """High-level runner executing audited IBTrACS ingestion.

    Args:
        pilot: If True, restricts ingestion to PILOT_STORMS (AMPHAN, BIPARJOY).
        file_path: Path to raw CSV (defaults to data/raw/ibtracs_ni_v04r01.csv).
        session_override: Optional active session (e.g. for testing).
        batch_size: Number of observations per SQL flush.

    Returns:
        The audited IngestionRun record.
    """
    if file_path is None or not file_path.is_file():
        csv_path, manifest = download_official_ibtracs_ni()
    else:
        csv_path = file_path
        from vayumarg.core.hashing import generate_manifest_record

        manifest = generate_manifest_record(csv_path, asset_type="RAW_CSV")

    sid_filter = set(PILOT_STORMS.keys()) if pilot else None

    def _ingest_step(session: Session, run_record: IngestionRun) -> tuple[int, int, int]:
        ds = get_or_create_data_source(session)
        run_record.data_source_id = ds.id

        asset = get_or_create_source_asset(session, ds.id, csv_path, manifest)
        run_record.source_asset_id = asset.id

        return ingest_ibtracs_data(
            session=session,
            source_asset=asset,
            file_path=csv_path,
            sid_filter=sid_filter,
            batch_size=batch_size,
        )

    if session_override is not None:
        ds = get_or_create_data_source(session_override)
        return execute_ingestion_transaction(
            data_source_id=ds.id,
            source_asset_id=None,
            ingest_fn=_ingest_step,
            session_override=session_override,
        )

    with get_db_session() as session:
        ds = get_or_create_data_source(session)
        run = execute_ingestion_transaction(
            data_source_id=ds.id,
            source_asset_id=None,
            ingest_fn=_ingest_step,
            session_override=session,
        )
        return run
