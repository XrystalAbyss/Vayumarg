"""Export interfaces and typed data contracts for scientific modules.

Strictly defines the scientific contracts consumed by:
1. Module A (Satellite-based current-state cyclone classification & intensity estimation):
   - Aligned synoptic timestamps for satellite raster pairing (INSAT-3D, MOSDAC, TCIR).
   - Multi-agency ground-truth wind speeds (IMD 3-min, JTWC 1-min, WMO 10-min) and categories.
2. Module B (Independent cyclone track and future wind-intensity forecasting):
   - Chronological sequence vectors (coordinates, translation velocity, intensities).
   - Explicit lineage flags distinguishing retrospective hindcast best-tracks from operational advisories.
   - Independence guarantee: Module B contracts do not depend on Module A predictions.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency
from vayumarg.database.schema import (
    SatelliteProcessedCrop,
    SatelliteTrackAssociation,
    Storm,
    StormAlias,
    TrackObservation,
)


class ModuleAExportRecord(BaseModel):
    """Scientific export contract for Module A satellite imagery alignment."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    storm_id: uuid.UUID
    sid: str = Field(..., description="Authoritative NOAA IBTrACS Storm Identifier")
    canonical_name: str
    season_year: int
    primary_basin: str

    observation_time_utc: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    # Multi-agency ground-truth intensity labels (NULL preserved when unobserved)
    imd_wind_speed_knots: float | None = Field(
        default=None, description="IMD 3-minute sustained maximum wind speed (kts)"
    )
    imd_category: str | None = Field(
        default=None, description="Official IMD cyclone intensity classification"
    )
    jtwc_wind_speed_knots: float | None = Field(
        default=None, description="JTWC 1-minute sustained maximum wind speed (kts)"
    )
    wmo_wind_speed_knots: float | None = Field(
        default=None, description="WMO consensus 10-minute sustained maximum wind speed (kts)"
    )
    central_pressure_hpa: float | None = Field(
        default=None, description="Minimum central surface pressure (hPa)"
    )

    is_retrospective_best_track: bool = Field(
        default=True,
        description="True for smoothed post-season best-track analyses, False for real-time bulletins",
    )
    satellite_matching_window_minutes: int = Field(
        default=30,
        description="Recommended temporal tolerance window for satellite raster alignment",
    )


class ModuleBTrajectoryPoint(BaseModel):
    """Individual chronological trajectory step for Module B sequence modeling."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    step_index: int
    observation_time_utc: datetime
    latitude: float
    longitude: float
    source_agency: str
    averaging_period: str
    wind_speed_knots: float | None = None
    central_pressure_hpa: float | None = None
    is_retrospective_best_track: bool = True


class ModuleBExportRecord(BaseModel):
    """Scientific export contract for Module B track and intensity forecasting."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    storm_id: uuid.UUID
    sid: str
    canonical_name: str
    season_year: int
    primary_basin: str
    total_trajectory_points: int
    trajectory: list[ModuleBTrajectoryPoint]


def export_module_a_dataset(
    session: Session,
    sid: str | None = None,
    season_year: int | None = None,
) -> list[ModuleAExportRecord]:
    """Extract synoptic observations structured specifically for Module A ground-truth pairing.

    Consolidates IBTrACS, IMD, and JTWC observations sharing the same storm and timestamp.
    """
    stmt = (
        select(TrackObservation, Storm, StormAlias.agency_storm_id)
        .join(Storm, TrackObservation.storm_id == Storm.id)
        .join(
            StormAlias,
            (StormAlias.storm_id == Storm.id) & (StormAlias.source_agency == Agency.IBTRACS.value),
        )
        .order_by(Storm.season_year, Storm.canonical_name, TrackObservation.observation_time_utc)
    )

    if sid:
        stmt = stmt.where(StormAlias.agency_storm_id == sid)
    if season_year:
        stmt = stmt.where(Storm.season_year == season_year)

    results = session.execute(stmt).all()

    # Group by (storm_id, observation_time_utc)
    grouped: dict[tuple[uuid.UUID, datetime], dict[str, Any]] = {}

    for obs, storm, storm_sid in results:
        key = (storm.id, obs.observation_time_utc)
        if key not in grouped:
            grouped[key] = {
                "storm_id": storm.id,
                "sid": storm_sid,
                "canonical_name": storm.canonical_name,
                "season_year": storm.season_year,
                "primary_basin": storm.primary_basin,
                "observation_time_utc": obs.observation_time_utc,
                "latitude": obs.latitude,
                "longitude": obs.longitude,
                "imd_wind_speed_knots": None,
                "imd_category": None,
                "jtwc_wind_speed_knots": None,
                "wmo_wind_speed_knots": None,
                "central_pressure_hpa": obs.central_pressure_hpa,
                "is_retrospective_best_track": obs.is_retrospective_best_track,
            }

        rec = grouped[key]
        if obs.source_agency == Agency.IMD.value:
            rec["imd_wind_speed_knots"] = obs.wind_speed_knots
            rec["imd_category"] = obs.imd_category
            if obs.central_pressure_hpa is not None:
                rec["central_pressure_hpa"] = obs.central_pressure_hpa
        elif obs.source_agency == Agency.JTWC.value:
            rec["jtwc_wind_speed_knots"] = obs.wind_speed_knots
            if rec["central_pressure_hpa"] is None and obs.central_pressure_hpa is not None:
                rec["central_pressure_hpa"] = obs.central_pressure_hpa
        elif obs.source_agency == Agency.IBTRACS.value:
            rec["wmo_wind_speed_knots"] = obs.wind_speed_knots
            if rec["central_pressure_hpa"] is None and obs.central_pressure_hpa is not None:
                rec["central_pressure_hpa"] = obs.central_pressure_hpa

    return [ModuleAExportRecord(**data) for data in grouped.values()]


def export_module_b_dataset(
    session: Session,
    sid: str | None = None,
    season_year: int | None = None,
    agency_preference: str = Agency.IBTRACS.value,
) -> list[ModuleBExportRecord]:
    """Extract chronological trajectory sequences structured specifically for Module B forecasting."""
    stmt = (
        select(TrackObservation, Storm, StormAlias.agency_storm_id)
        .join(Storm, TrackObservation.storm_id == Storm.id)
        .join(
            StormAlias,
            (StormAlias.storm_id == Storm.id) & (StormAlias.source_agency == Agency.IBTRACS.value),
        )
        .where(TrackObservation.source_agency == agency_preference)
        .order_by(Storm.id, TrackObservation.observation_time_utc)
    )

    if sid:
        stmt = stmt.where(StormAlias.agency_storm_id == sid)
    if season_year:
        stmt = stmt.where(Storm.season_year == season_year)

    results = session.execute(stmt).all()

    storms_map: dict[uuid.UUID, dict[str, Any]] = {}
    for obs, storm, storm_sid in results:
        if storm.id not in storms_map:
            storms_map[storm.id] = {
                "storm_id": storm.id,
                "sid": storm_sid,
                "canonical_name": storm.canonical_name,
                "season_year": storm.season_year,
                "primary_basin": storm.primary_basin,
                "points": [],
            }

        storms_map[storm.id]["points"].append(
            ModuleBTrajectoryPoint(
                step_index=len(storms_map[storm.id]["points"]),
                observation_time_utc=obs.observation_time_utc,
                latitude=obs.latitude,
                longitude=obs.longitude,
                source_agency=obs.source_agency,
                averaging_period=obs.averaging_period,
                wind_speed_knots=obs.wind_speed_knots,
                central_pressure_hpa=obs.central_pressure_hpa,
                is_retrospective_best_track=obs.is_retrospective_best_track,
            )
        )

    return [
        ModuleBExportRecord(
            storm_id=data["storm_id"],
            sid=data["sid"],
            canonical_name=data["canonical_name"],
            season_year=data["season_year"],
            primary_basin=data["primary_basin"],
            total_trajectory_points=len(data["points"]),
            trajectory=data["points"],
        )
        for data in storms_map.values()
    ]


class SatellitePairedExportRecord(BaseModel):
    """Pairing contract for Module A satellite image patch and ground-truth track label."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    association_id: uuid.UUID
    crop_id: uuid.UUID
    storm_id: uuid.UUID
    sid: str
    canonical_name: str
    crop_time_utc: datetime
    track_time_utc: datetime
    temporal_offset_minutes: float
    spatial_offset_km: float
    association_confidence: float
    verification_status: str
    channels: list[str]
    storage_uri: str
    center_latitude: float
    center_longitude: float
    source_agency: str
    averaging_period: str
    wind_speed_knots: float | None = None
    imd_category: str | None = None
    central_pressure_hpa: float | None = None


def export_satellite_paired_dataset(
    session: Session,
    sid: str | None = None,
    season_year: int | None = None,
    verification_status: str = "REAL_VERIFIED",
    min_confidence: float = 0.5,
) -> list[SatellitePairedExportRecord]:
    """Export satellite-to-track paired training records with mandatory provenance verification enforcement."""
    stmt = (
        select(
            SatelliteTrackAssociation,
            SatelliteProcessedCrop,
            TrackObservation,
            Storm,
            StormAlias.agency_storm_id,
        )
        .join(
            SatelliteProcessedCrop, SatelliteTrackAssociation.crop_id == SatelliteProcessedCrop.id
        )
        .join(
            TrackObservation, SatelliteTrackAssociation.track_observation_id == TrackObservation.id
        )
        .join(Storm, SatelliteProcessedCrop.storm_id == Storm.id)
        .join(
            StormAlias,
            (StormAlias.storm_id == Storm.id) & (StormAlias.source_agency == Agency.IBTRACS.value),
        )
        .where(
            SatelliteTrackAssociation.verification_status == verification_status,
            SatelliteTrackAssociation.association_confidence >= min_confidence,
        )
        .order_by(SatelliteProcessedCrop.crop_time_utc)
    )

    if sid:
        stmt = stmt.where(StormAlias.agency_storm_id == sid)
    if season_year:
        stmt = stmt.where(Storm.season_year == season_year)

    rows = session.execute(stmt).all()
    results = []
    for assoc, crop, obs, storm, storm_sid in rows:
        results.append(
            SatellitePairedExportRecord(
                association_id=assoc.id,
                crop_id=crop.id,
                storm_id=storm.id,
                sid=storm_sid,
                canonical_name=storm.canonical_name,
                crop_time_utc=crop.crop_time_utc,
                track_time_utc=obs.observation_time_utc,
                temporal_offset_minutes=assoc.temporal_offset_minutes,
                spatial_offset_km=assoc.spatial_offset_km,
                association_confidence=assoc.association_confidence,
                verification_status=assoc.verification_status,
                channels=crop.channels,
                storage_uri=crop.storage_uri,
                center_latitude=crop.center_latitude,
                center_longitude=crop.center_longitude,
                source_agency=obs.source_agency,
                averaging_period=obs.averaging_period,
                wind_speed_knots=obs.wind_speed_knots,
                imd_category=obs.imd_category,
                central_pressure_hpa=obs.central_pressure_hpa,
            )
        )
    return results


class ModuleAMultichannelExportRecord(BaseModel):
    """Canonical ML-ready training sample contract for Module A with multi-channel and multi-agency segregation.

    Deduplicates satellite frames by making the image crop the primary atomic sample.
    Stores authoritative IMD ground-truth (3-min sustained wind) as primary label,
    with JTWC (1-min sustained wind) as secondary label on the same record to prevent frame duplication.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    crop_id: uuid.UUID
    granule_id: uuid.UUID
    storm_id: uuid.UUID
    sid: str
    canonical_name: str
    season_year: int
    primary_basin: str

    crop_time_utc: datetime
    track_time_utc: datetime
    temporal_offset_minutes: float
    spatial_offset_km: float

    channels: list[str]
    storage_uri: str
    center_latitude: float
    center_longitude: float
    pixel_height: int
    pixel_width: int
    spatial_resolution_km: float

    # Canonical primary label (IMD 3-min MSW)
    primary_agency: str = "IMD"
    primary_wind_speed_knots: float | None = None
    primary_imd_category: str | None = None
    central_pressure_hpa: float | None = None

    # Secondary / alternative label (JTWC 1-min MSW) on same frame
    secondary_agency: str | None = None
    secondary_wind_speed_knots: float | None = None

    # Scientific eligibility and provenance governance
    provenance_status: str
    model_eligibility: str
    quality_flags: dict[str, Any] | None = None


def export_module_a_multichannel_dataset(
    session: Session,
    sid: str | None = None,
    season_year: int | None = None,
    min_model_eligibility: str = "MODEL_ELIGIBLE",
) -> list[ModuleAMultichannelExportRecord]:
    """Export canonical, deduplicated Module A image crops with segregated multi-agency labels."""
    from vayumarg.contracts.enums import ModelEligibility

    # Query all valid crops and their associations
    stmt = (
        select(
            SatelliteProcessedCrop,
            SatelliteTrackAssociation,
            TrackObservation,
            Storm,
            StormAlias.agency_storm_id,
        )
        .join(
            SatelliteTrackAssociation,
            SatelliteTrackAssociation.crop_id == SatelliteProcessedCrop.id,
        )
        .join(
            TrackObservation,
            SatelliteTrackAssociation.track_observation_id == TrackObservation.id,
        )
        .join(Storm, SatelliteProcessedCrop.storm_id == Storm.id)
        .join(
            StormAlias,
            (StormAlias.storm_id == Storm.id) & (StormAlias.source_agency == Agency.IBTRACS.value),
        )
        .order_by(SatelliteProcessedCrop.crop_time_utc)
    )

    if sid:
        stmt = stmt.where(StormAlias.agency_storm_id == sid)
    if season_year:
        stmt = stmt.where(Storm.season_year == season_year)

    rows = session.execute(stmt).all()

    # Group by crop_id to prevent multiple rows per image frame
    crops_map: dict[uuid.UUID, dict[str, Any]] = {}

    for crop, assoc, obs, storm, storm_sid in rows:
        cid = crop.id
        if cid not in crops_map:
            crops_map[cid] = {
                "crop": crop,
                "storm": storm,
                "sid": storm_sid,
                "imd_obs": None,
                "jtwc_obs": None,
                "best_assoc": assoc,
            }

        if obs.source_agency == "IMD":
            crops_map[cid]["imd_obs"] = obs
            crops_map[cid]["best_assoc"] = assoc
        elif obs.source_agency == "JTWC":
            crops_map[cid]["jtwc_obs"] = obs

    export_records: list[ModuleAMultichannelExportRecord] = []

    for entry in crops_map.values():
        crop = entry["crop"]
        storm = entry["storm"]
        imd_obs = entry["imd_obs"]
        jtwc_obs = entry["jtwc_obs"]
        assoc = entry["best_assoc"]

        provenance = getattr(crop, "verification_status", "PROVENANCE_UNVERIFIED")

        # Evaluate model eligibility
        if provenance == "SYNTHETIC_FIXTURE":
            eligibility = ModelEligibility.SYNTHETIC_FIXTURE.value
        elif provenance in ("REAL_VERIFIED", "AUTHENTIC_SOURCE_VERIFIED"):
            # If IMD observation exists within tolerance and crop is valid on disk
            if (
                imd_obs
                and assoc.temporal_offset_minutes <= 30.0
                and assoc.spatial_offset_km <= 50.0
            ):
                eligibility = ModelEligibility.MODEL_ELIGIBLE.value
            elif imd_obs:
                eligibility = ModelEligibility.RESEARCH_HOLD.value
            else:
                eligibility = ModelEligibility.INELIGIBLE.value
        else:
            eligibility = ModelEligibility.INELIGIBLE.value

        # Filter by requested eligibility
        if (
            min_model_eligibility == "MODEL_ELIGIBLE"
            and eligibility != ModelEligibility.MODEL_ELIGIBLE.value
        ):
            continue

        primary_wind = imd_obs.wind_speed_knots if imd_obs else None
        primary_cat = imd_obs.imd_category if imd_obs else None
        pres = imd_obs.central_pressure_hpa if imd_obs else None
        track_time = (
            imd_obs.observation_time_utc
            if imd_obs
            else (jtwc_obs.observation_time_utc if jtwc_obs else crop.crop_time_utc)
        )

        sec_agency = "JTWC" if jtwc_obs else None
        sec_wind = jtwc_obs.wind_speed_knots if jtwc_obs else None

        record = ModuleAMultichannelExportRecord(
            crop_id=crop.id,
            granule_id=crop.granule_id,
            storm_id=storm.id,
            sid=entry["sid"],
            canonical_name=storm.canonical_name,
            season_year=storm.season_year,
            primary_basin=storm.primary_basin,
            crop_time_utc=crop.crop_time_utc,
            track_time_utc=track_time,
            temporal_offset_minutes=assoc.temporal_offset_minutes,
            spatial_offset_km=assoc.spatial_offset_km,
            channels=crop.channels,
            storage_uri=crop.storage_uri,
            center_latitude=crop.center_latitude,
            center_longitude=crop.center_longitude,
            pixel_height=crop.pixel_height,
            pixel_width=crop.pixel_width,
            spatial_resolution_km=crop.spatial_resolution_km,
            primary_agency="IMD",
            primary_wind_speed_knots=primary_wind,
            primary_imd_category=primary_cat,
            central_pressure_hpa=pres,
            secondary_agency=sec_agency,
            secondary_wind_speed_knots=sec_wind,
            provenance_status=provenance,
            model_eligibility=eligibility,
            quality_flags=crop.quality_control_flags,
        )
        export_records.append(record)

    return export_records
