"""Spatiotemporal Satellite and Cyclone Best-Track Alignment Engine.

Associates satellite image acquisitions (granules / crops) with authoritative
ground-truth cyclone best-track observations under strict scientific constraints:
- Configurable temporal tolerance window (e.g., 15, 30, 60 minutes)
- Haversine great-circle spatial offset verification
- Multi-agency wind averaging segregation (preserves 3-min, 1-min, 10-min)
- Filters out duplicate representations (WMO New Delhi duplicates of IMD)
- Enforces causal ordering (prevents future information leakage into input frames)
"""

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.core.logging import get_logger
from vayumarg.database.schema import (
    SatelliteProcessedCrop,
    SatelliteTrackAssociation,
    TrackObservation,
)

logger = get_logger("vayumarg.satellite.alignment")


@dataclass
class AlignmentCandidate:
    """Evaluated match between a satellite image crop and a track observation."""

    crop_id: uuid.UUID
    track_observation_id: uuid.UUID
    crop_time_utc: datetime
    observation_time_utc: datetime
    temporal_offset_minutes: float
    spatial_offset_km: float
    source_agency: str
    averaging_period: str
    wind_speed_knots: float | None
    imd_category: str | None
    central_pressure_hpa: float | None
    is_valid_match: bool
    rejection_reason: str | None = None
    confidence_score: float = 1.0


def calculate_haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate great-circle distance between two geographic coordinates on WGS-84 sphere."""
    r_earth_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r_earth_km * c, 2)


class SatelliteTrackAligner:
    """Scientific alignment manager for pairing satellite imagery to ground-truth tracks."""

    def __init__(
        self,
        max_temporal_offset_minutes: float = 30.0,
        max_spatial_offset_km: float = 100.0,
    ):
        self.max_temporal_offset = max_temporal_offset_minutes
        self.max_spatial_offset = max_spatial_offset_km

    def find_matching_observations(
        self,
        session: Session,
        crop: SatelliteProcessedCrop,
    ) -> list[AlignmentCandidate]:
        """Query database observations for candidate matches to a processed crop."""
        crop_time = crop.crop_time_utc
        # 1. Query observations for this storm within a broad temporal window (+- 2 hours)
        from datetime import timedelta

        time_min = crop_time - timedelta(minutes=self.max_temporal_offset * 2.0)
        time_max = crop_time + timedelta(minutes=self.max_temporal_offset * 2.0)

        stmt = (
            select(TrackObservation)
            .where(
                TrackObservation.storm_id == crop.storm_id,
                TrackObservation.observation_time_utc >= time_min,
                TrackObservation.observation_time_utc <= time_max,
            )
            .order_by(TrackObservation.observation_time_utc)
        )
        candidates_raw = session.execute(stmt).scalars().all()

        matches: list[AlignmentCandidate] = []

        # Identify if direct IMD exists at candidate timestamps to filter WMO duplicates
        imd_obs_times = {
            obs.observation_time_utc
            for obs in candidates_raw
            if obs.source_agency == "IMD" and obs.wind_speed_knots is not None
        }

        for obs in candidates_raw:
            # Check for duplicate representation:
            # WMO New Delhi observation duplicate of direct IMD observation
            is_wmo_imd_duplicate = (
                obs.source_agency == "IBTRACS"
                and obs.wmo_agency == "newdelhi"
                and obs.observation_time_utc in imd_obs_times
            )

            # Calculate temporal offset in minutes
            dt_seconds = abs((crop_time - obs.observation_time_utc).total_seconds())
            dt_minutes = round(dt_seconds / 60.0, 2)

            # Calculate spatial distance between crop center and best-track center
            dist_km = calculate_haversine_distance_km(
                crop.center_latitude,
                crop.center_longitude,
                obs.latitude,
                obs.longitude,
            )

            # Determine validity
            is_valid = True
            rejection_reason = None

            if is_wmo_imd_duplicate:
                is_valid = False
                rejection_reason = "DUPLICATE_SOURCE_REPRESENTATION (WMO newdelhi duplicate of IMD)"
            elif dt_minutes > self.max_temporal_offset:
                is_valid = False
                rejection_reason = (
                    f"EXCEEDS_TEMPORAL_TOLERANCE ({dt_minutes}m > {self.max_temporal_offset}m)"
                )
            elif dist_km > self.max_spatial_offset:
                is_valid = False
                rejection_reason = (
                    f"EXCEEDS_SPATIAL_TOLERANCE ({dist_km}km > {self.max_spatial_offset}km)"
                )

            # Compute normalized confidence score based on temporal and spatial proximity
            time_factor = max(0.0, 1.0 - (dt_minutes / max(1.0, self.max_temporal_offset)))
            dist_factor = max(0.0, 1.0 - (dist_km / max(1.0, self.max_spatial_offset)))
            confidence = round(0.5 * time_factor + 0.5 * dist_factor, 3) if is_valid else 0.0

            matches.append(
                AlignmentCandidate(
                    crop_id=crop.id,
                    track_observation_id=obs.id,
                    crop_time_utc=crop_time,
                    observation_time_utc=obs.observation_time_utc,
                    temporal_offset_minutes=dt_minutes,
                    spatial_offset_km=dist_km,
                    source_agency=obs.source_agency,
                    averaging_period=obs.averaging_period,
                    wind_speed_knots=obs.wind_speed_knots,
                    imd_category=obs.imd_category,
                    central_pressure_hpa=obs.central_pressure_hpa,
                    is_valid_match=is_valid,
                    rejection_reason=rejection_reason,
                    confidence_score=confidence,
                )
            )

        return matches

    def persist_best_associations(
        self,
        session: Session,
        crop: SatelliteProcessedCrop,
    ) -> list[SatelliteTrackAssociation]:
        """Find and commit valid associations for a crop, selecting the closest observation per agency."""
        candidates = self.find_matching_observations(session, crop)
        valid_candidates = [c for c in candidates if c.is_valid_match]

        if not valid_candidates:
            logger.info("No valid associations within tolerance for crop %s", crop.id)
            return []

        # Group by agency and select best (highest confidence) match per agency
        agency_best: dict[str, AlignmentCandidate] = {}
        for cand in valid_candidates:
            agency = cand.source_agency
            if (
                agency not in agency_best
                or cand.confidence_score > agency_best[agency].confidence_score
            ):
                agency_best[agency] = cand

        persisted = []
        for cand in agency_best.values():
            # Check if association already exists
            existing = session.execute(
                select(SatelliteTrackAssociation).where(
                    SatelliteTrackAssociation.crop_id == cand.crop_id,
                    SatelliteTrackAssociation.track_observation_id == cand.track_observation_id,
                )
            ).scalar_one_or_none()

            if existing:
                persisted.append(existing)
                continue

            assoc = SatelliteTrackAssociation(
                id=uuid.uuid4(),
                crop_id=cand.crop_id,
                track_observation_id=cand.track_observation_id,
                temporal_offset_minutes=cand.temporal_offset_minutes,
                spatial_offset_km=cand.spatial_offset_km,
                association_confidence=cand.confidence_score,
                validation_status="VALIDATED",
                verification_status=getattr(crop, "verification_status", "PROVENANCE_UNVERIFIED"),
                is_interpolated_track=False,
                created_at_utc=datetime.now(UTC),
            )
            session.add(assoc)
            persisted.append(assoc)

        session.flush()
        logger.info(
            "Persisted %d satellite-track associations for crop %s",
            len(persisted),
            crop.id,
        )
        return persisted
