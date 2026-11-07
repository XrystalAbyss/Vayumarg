"""Reproducible Dataset Freeze and Snapshot Management for Vayumarg.

Creates immutable, cryptographically verified dataset snapshot records in
the `dataset_snapshots` table and writes matching manifest files to disk.
Enforces reproducibility for Module A (satellite pairing) and Module B (forecasting).
"""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vayumarg.core.hashing import calculate_sha256
from vayumarg.core.logging import get_logger
from vayumarg.database.schema import (
    DataQualityIssue,
    DatasetSnapshot,
    SourceAsset,
    Storm,
    TrackObservation,
)

logger = get_logger("vayumarg.quality.snapshot")

DEFAULT_MANIFEST_PATH = Path("data/manifests/vayumarg_f1_1_freeze_manifest.json")
DEFAULT_SNAPSHOT_NAME = "vayumarg-nio-ibtracs-f1.1-freeze"
DEFAULT_TRANSFORMATION_VERSION = "f1.1"


def build_snapshot_manifest(
    session: Session,
    snapshot_name: str = DEFAULT_SNAPSHOT_NAME,
    transformation_version: str = DEFAULT_TRANSFORMATION_VERSION,
) -> dict[str, Any]:
    """Compile a comprehensive cryptographic manifest from the current database state."""
    # 1. Total counts
    total_obs = session.execute(select(func.count(TrackObservation.id))).scalar_one()
    total_storms = session.execute(select(func.count(Storm.id))).scalar_one()

    # 2. Temporal coverage
    time_bounds = session.execute(
        select(
            func.min(TrackObservation.observation_time_utc),
            func.max(TrackObservation.observation_time_utc),
        )
    ).one()
    min_time = time_bounds[0].isoformat() if time_bounds[0] else None
    max_time = time_bounds[1].isoformat() if time_bounds[1] else None

    # 3. Agency breakdown
    agency_counts_raw = session.execute(
        select(TrackObservation.source_agency, func.count(TrackObservation.id)).group_by(
            TrackObservation.source_agency
        )
    ).all()
    agency_counts = {row[0]: row[1] for row in agency_counts_raw}

    # 4. Averaging period distribution
    avg_counts_raw = session.execute(
        select(TrackObservation.averaging_period, func.count(TrackObservation.id)).group_by(
            TrackObservation.averaging_period
        )
    ).all()
    avg_counts = {row[0]: row[1] for row in avg_counts_raw}

    # 5. Quality flag distribution
    qflag_counts_raw = session.execute(
        select(TrackObservation.quality_flag, func.count(TrackObservation.id)).group_by(
            TrackObservation.quality_flag
        )
    ).all()
    qflags = {row[0]: row[1] for row in qflag_counts_raw}

    # 6. Quality issues count
    issues_count = session.execute(select(func.count(DataQualityIssue.id))).scalar_one()

    # 7. Source assets
    assets_raw = session.execute(select(SourceAsset)).scalars().all()
    source_assets = [
        {
            "id": str(a.id),
            "asset_type": a.asset_type,
            "artifact_uri": a.artifact_uri,
            "sha256": a.sha256_checksum,
            "size_bytes": a.file_size_bytes,
            "retrieval_time_utc": a.retrieval_time_utc.isoformat()
            if a.retrieval_time_utc
            else None,
        }
        for a in assets_raw
    ]

    manifest = {
        "manifest_name": snapshot_name,
        "transformation_version": transformation_version,
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "dataset_scope": {
            "basin": "NI",
            "source": "NOAA_IBTrACS_v04r01",
            "time_range": {
                "start_utc": min_time,
                "end_utc": max_time,
            },
        },
        "totals": {
            "total_storms": total_storms,
            "total_observations": total_obs,
            "persisted_quality_issues": issues_count,
        },
        "distributions": {
            "source_agency": agency_counts,
            "averaging_period": avg_counts,
            "quality_flag": qflags,
        },
        "source_assets": source_assets,
        "module_readiness": {
            "module_a_current_state": {
                "compatible_agencies": ["IMD", "IBTRACS", "JTWC"],
                "supported_averaging_periods": ["3-min", "1-min", "10-min"],
                "requires_satellite_pairing": True,
            },
            "module_b_forecasting": {
                "compatible_agencies": ["IMD", "JTWC", "IBTRACS"],
                "synoptic_interval_hours": [3, 6],
                "independent_of_module_a": True,
            },
        },
    }
    return manifest


def freeze_dataset_snapshot(
    session: Session,
    snapshot_name: str = DEFAULT_SNAPSHOT_NAME,
    transformation_version: str = DEFAULT_TRANSFORMATION_VERSION,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    force: bool = False,
) -> DatasetSnapshot:
    """Freeze current database state into a cryptographic manifest file and database record."""
    if not force:
        existing = (
            session.execute(
                select(DatasetSnapshot).where(
                    DatasetSnapshot.snapshot_name == snapshot_name,
                    DatasetSnapshot.transformation_version == transformation_version,
                )
            )
            .scalars()
            .first()
        )
        if existing:
            logger.info(
                "DatasetSnapshot already exists for %s (%s): %s",
                snapshot_name,
                transformation_version,
                existing.id,
            )
            return existing

    target_path = Path(manifest_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_data = build_snapshot_manifest(
        session=session,
        snapshot_name=snapshot_name,
        transformation_version=transformation_version,
    )

    # Write manifest JSON deterministically
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)

    # Compute manifest SHA-256
    manifest_sha256 = calculate_sha256(target_path)
    logger.info("Manifest written to %s (SHA-256: %s)", target_path, manifest_sha256)

    total_samples = manifest_data["totals"]["total_observations"]
    filter_criteria = {
        "basin": "NI",
        "transformation_version": transformation_version,
        "dataset_scope": manifest_data["dataset_scope"],
    }

    # Query existing snapshot with matching unique constraint
    existing = session.execute(
        select(DatasetSnapshot).where(
            DatasetSnapshot.snapshot_name == snapshot_name,
            DatasetSnapshot.transformation_version == transformation_version,
            DatasetSnapshot.manifest_sha256 == manifest_sha256,
        )
    ).scalar_one_or_none()

    if existing:
        logger.info("DatasetSnapshot already exists with matching SHA-256: %s", existing.id)
        return existing

    snapshot = DatasetSnapshot(
        id=uuid.uuid4(),
        snapshot_name=snapshot_name,
        transformation_version=transformation_version,
        manifest_sha256=manifest_sha256,
        total_samples=total_samples,
        filter_criteria=filter_criteria,
        manifest_uri=str(target_path.as_posix()),
        created_at_utc=datetime.now(UTC),
    )
    session.add(snapshot)
    session.flush()

    logger.info("Created DatasetSnapshot record: %s", snapshot.id)
    return snapshot
