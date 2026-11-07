"""Scientific Data Reconciliation Engine for Vayumarg.

Resolves critical scientific metadata discrepancies:
1. Reconciles WMO_WIND averaging period based on authoritative WMO_AGENCY provenance.
2. Distinguishes WMO-adopted agency estimates from independent consensus measurements.
3. Classifies IMD category populations (with vs without wind) with separate denominators.
4. Identifies cross-basin tracks and records meaningful scientific DataQualityIssues.
5. Produces comprehensive Before/After audit diffs serialized to reports/F1_1_BEFORE_AFTER_AUDIT.json.
"""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency, IssueSeverity, ResolutionStatus
from vayumarg.core.logging import get_logger
from vayumarg.database.schema import (
    DataQualityIssue,
    SourceAsset,
    Storm,
    TrackObservation,
)

logger = get_logger("vayumarg.quality.reconciliation")


def audit_state(session: Session) -> dict[str, Any]:
    """Capture a comprehensive scientific audit snapshot of the current database state."""
    # 1. Total counts
    total_obs = session.execute(select(func.count(TrackObservation.id))).scalar_one()
    total_storms = session.execute(select(func.count(Storm.id))).scalar_one()

    # 2. Averaging period distribution
    avg_counts_raw = session.execute(
        select(TrackObservation.averaging_period, func.count(TrackObservation.id)).group_by(
            TrackObservation.averaging_period
        )
    ).all()
    avg_counts = {row[0]: row[1] for row in avg_counts_raw}

    # 3. Non-null wind by agency
    wind_counts_raw = session.execute(
        select(TrackObservation.source_agency, func.count(TrackObservation.id))
        .where(TrackObservation.wind_speed_knots.is_not(None))
        .group_by(TrackObservation.source_agency)
    ).all()
    wind_counts = {row[0]: row[1] for row in wind_counts_raw}

    # 4. WMO Agency distribution
    wmo_agencies_raw = session.execute(
        select(TrackObservation.wmo_agency, func.count(TrackObservation.id))
        .where(TrackObservation.source_agency == Agency.IBTRACS.value)
        .group_by(TrackObservation.wmo_agency)
    ).all()
    wmo_agency_counts = {(row[0] or "None"): row[1] for row in wmo_agencies_raw}

    # 5. IMD Four-Way Venn Reconciliation
    imd_total = session.execute(
        select(func.count(TrackObservation.id)).where(
            TrackObservation.source_agency == Agency.IMD.value
        )
    ).scalar_one()

    imd_both = session.execute(
        select(func.count(TrackObservation.id)).where(
            TrackObservation.source_agency == Agency.IMD.value,
            TrackObservation.wind_speed_knots.is_not(None),
            TrackObservation.imd_category.is_not(None),
        )
    ).scalar_one()

    imd_cat_only = session.execute(
        select(func.count(TrackObservation.id)).where(
            TrackObservation.source_agency == Agency.IMD.value,
            TrackObservation.wind_speed_knots.is_(None),
            TrackObservation.imd_category.is_not(None),
        )
    ).scalar_one()

    imd_wind_only = session.execute(
        select(func.count(TrackObservation.id)).where(
            TrackObservation.source_agency == Agency.IMD.value,
            TrackObservation.wind_speed_knots.is_not(None),
            TrackObservation.imd_category.is_(None),
        )
    ).scalar_one()

    imd_neither = session.execute(
        select(func.count(TrackObservation.id)).where(
            TrackObservation.source_agency == Agency.IMD.value,
            TrackObservation.wind_speed_knots.is_(None),
            TrackObservation.imd_category.is_(None),
        )
    ).scalar_one()

    # 6. Quality flag breakdown
    qflags_raw = session.execute(
        select(TrackObservation.quality_flag, func.count(TrackObservation.id)).group_by(
            TrackObservation.quality_flag
        )
    ).all()
    qflags = {row[0]: row[1] for row in qflags_raw}

    # 7. Quality issues table count
    total_quality_issues = session.execute(select(func.count(DataQualityIssue.id))).scalar_one()

    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "total_storms": total_storms,
        "total_observations": total_obs,
        "averaging_periods": avg_counts,
        "non_null_wind_by_agency": wind_counts,
        "wmo_agency_provenance": wmo_agency_counts,
        "imd_reconciliation": {
            "total_imd_observations": imd_total,
            "both_wind_and_category": imd_both,
            "category_only_null_wind": imd_cat_only,
            "wind_only_null_category": imd_wind_only,
            "neither_wind_nor_category": imd_neither,
            "sum_check": (imd_both + imd_cat_only + imd_wind_only + imd_neither == imd_total),
        },
        "quality_flags": qflags,
        "persisted_quality_issues_count": total_quality_issues,
    }


def execute_scientific_reconciliation(session: Session) -> dict[str, Any]:
    """Execute transactional, reversible scientific data reconciliation on existing observations."""
    logger.info("Capturing PRE-reconciliation database audit...")
    before_state = audit_state(session)

    # Step 1: Populate wmo_agency from raw_payload for IBTRACS observations
    logger.info("Step 1: Synchronizing wmo_agency provenance from raw_payload...")
    session.execute(
        text(
            """
            UPDATE track_observations
            SET wmo_agency = raw_payload->>'wmo_agency'
            WHERE source_agency = 'IBTRACS'
              AND raw_payload->>'wmo_agency' IS NOT NULL;
            """
        )
    )

    # Step 2: Correct averaging_period for IBTRACS observations based on authoritative WMO_AGENCY
    logger.info("Step 2: Correcting WMO_WIND averaging periods based on WMO_AGENCY...")
    # 2a. RSMC New Delhi (IMD) convention = 3-min
    session.execute(
        text(
            """
            UPDATE track_observations
            SET averaging_period = '3-min'
            WHERE source_agency = 'IBTRACS'
              AND wmo_agency = 'newdelhi'
              AND wind_speed_knots IS NOT NULL;
            """
        )
    )

    # 2b. RSMC Tokyo (JMA) convention = 10-min
    session.execute(
        text(
            """
            UPDATE track_observations
            SET averaging_period = '10-min'
            WHERE source_agency = 'IBTRACS'
              AND wmo_agency = 'tokyo'
              AND wind_speed_knots IS NOT NULL;
            """
        )
    )

    # 2c. USA NHC / JTWC convention = 1-min
    session.execute(
        text(
            """
            UPDATE track_observations
            SET averaging_period = '1-min'
            WHERE source_agency = 'IBTRACS'
              AND wmo_agency IN ('hurdat_atl', 'atcf')
              AND wind_speed_knots IS NOT NULL;
            """
        )
    )

    # 2d. Observations with NULL wind speed -> averaging period is unknown
    session.execute(
        text(
            """
            UPDATE track_observations
            SET averaging_period = 'unknown'
            WHERE wind_speed_knots IS NULL;
            """
        )
    )

    # Step 3: Flag cross-basin observations
    logger.info("Step 3: Classifying cross-basin track observations...")
    session.execute(
        text(
            """
            UPDATE track_observations
            SET quality_flag = 'CROSS_BASIN'
            WHERE latitude > 40.0 OR longitude < 30.0 OR longitude > 105.0;
            """
        )
    )

    # Step 4: Persist structured scientific DataQualityIssue entries
    logger.info("Step 4: Persisting meaningful DataQualityIssue records...")
    # Clean any stale open issues to guarantee idempotency
    session.execute(text("DELETE FROM data_quality_issues;"))

    asset = session.execute(select(SourceAsset)).scalars().first()
    asset_id = asset.id if asset else None

    # Issue 1: Cross-basin tracks
    cross_basin_count = session.execute(
        text("SELECT count(*) FROM track_observations WHERE quality_flag = 'CROSS_BASIN';")
    ).scalar()

    issue_cb = DataQualityIssue(
        id=uuid.uuid4(),
        source_asset_id=asset_id,
        severity=IssueSeverity.WARNING.value,
        cause="CROSS_BASIN_TRACK_POINTS",
        details={
            "description": "Synoptic track points recorded outside the regional North Indian Ocean bounding box (0-40N, 30-105E). Includes Western Pacific transits and Arctic extratropical transitions.",
            "observation_count": cross_basin_count,
            "bounding_box_filter": "latitude > 40.0 OR longitude < 30.0 OR longitude > 105.0",
        },
        resolution_status=ResolutionStatus.ACCEPTED_EXCEPTION.value,
        created_at_utc=datetime.now(UTC),
    )
    session.add(issue_cb)

    # Issue 2: Pre-modern historical uninstrumented cyclones
    hist_storms = session.execute(
        text("SELECT count(*) FROM storms WHERE season_year < 1900;")
    ).scalar()

    issue_hist = DataQualityIssue(
        id=uuid.uuid4(),
        source_asset_id=asset_id,
        severity=IssueSeverity.INFO.value,
        cause="HISTORICAL_UNINSTRUMENTED_ERA",
        details={
            "description": "Cyclones from seasons 1842-1899 compiled from ship logs and historical maritime records lacking standardized surface wind and central pressure measurements.",
            "storm_count": hist_storms,
            "policy": "Preserved with strict SQL NULL without zero-coercion.",
        },
        resolution_status=ResolutionStatus.ACCEPTED_EXCEPTION.value,
        created_at_utc=datetime.now(UTC),
    )
    session.add(issue_hist)

    # Issue 3: Unnamed cyclone density
    unnamed_storms = session.execute(
        text("SELECT count(*) FROM storms WHERE canonical_name = 'UNNAMED';")
    ).scalar()

    issue_unnamed = DataQualityIssue(
        id=uuid.uuid4(),
        source_asset_id=asset_id,
        severity=IssueSeverity.INFO.value,
        cause="UNNAMED_CYCLONE_POPULATION",
        details={
            "description": "Cyclonic systems un-named prior to WMO/ESCAP PTC 2004 naming policy, indexed by authoritative IBTrACS SIDs.",
            "unnamed_storm_count": unnamed_storms,
            "policy": "Tracked via immutable internal UUIDs and authoritative source aliases.",
        },
        resolution_status=ResolutionStatus.ACCEPTED_EXCEPTION.value,
        created_at_utc=datetime.now(UTC),
    )
    session.add(issue_unnamed)

    # Issue 4: Representative sample issues for extreme cross-basin cases (e.g. Hurricane Faith 83N, 1932 NA transit)
    extreme_obs = session.execute(
        text(
            "SELECT id, latitude, longitude FROM track_observations WHERE latitude >= 80.0 LIMIT 5;"
        )
    ).all()
    for row in extreme_obs:
        obs_issue = DataQualityIssue(
            id=uuid.uuid4(),
            source_asset_id=asset_id,
            track_observation_id=row[0],
            severity=IssueSeverity.INFO.value,
            cause="ARCTIC_EXTRATROPICAL_TRANSITION",
            details={
                "description": "Atlantic cyclone extratropical transit crossing into Siberian/Arctic sector of NI basin.",
                "latitude": row[1],
                "longitude": row[2],
            },
            resolution_status=ResolutionStatus.ACCEPTED_EXCEPTION.value,
            created_at_utc=datetime.now(UTC),
        )
        session.add(obs_issue)

    session.flush()

    logger.info("Capturing POST-reconciliation database audit...")
    after_state = audit_state(session)

    diff = {
        "reconciliation_executed_at_utc": datetime.now(UTC).isoformat(),
        "database_target": session.bind.url.database if session.bind else "unknown",
        "before": before_state,
        "after": after_state,
        "impact_summary": {
            "wmo_wind_observations_corrected_to_3min_imd": after_state["averaging_periods"].get(
                "3-min", 0
            )
            - before_state["averaging_periods"].get("3-min", 0),
            "wmo_wind_observations_retained_as_10min_tokyo": after_state["averaging_periods"].get(
                "10-min", 0
            ),
            "wmo_wind_observations_corrected_to_1min_usa": after_state["averaging_periods"].get(
                "1-min", 0
            )
            - before_state["averaging_periods"].get("1-min", 0),
            "null_wind_observations_corrected_to_unknown": after_state["averaging_periods"].get(
                "unknown", 0
            ),
            "cross_basin_observations_flagged": after_state["quality_flags"].get("CROSS_BASIN", 0),
            "data_quality_issues_persisted": after_state["persisted_quality_issues_count"],
        },
    }

    report_path = Path("reports/F1_1_BEFORE_AFTER_AUDIT.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(diff, f, indent=2)

    logger.info("Reconciliation complete. Audit diff written to %s", report_path)
    return diff
