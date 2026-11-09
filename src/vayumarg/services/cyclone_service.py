"""Cyclone metadata, track queries, and catalog service.

Provides robust multi-agency historical observations with automatic fallback to offline demonstration caches.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import Storm, StormAlias, TrackObservation
from vayumarg.module_b.forecast_engine import (
    resolve_storm_in_database,
    validate_and_clean_observations,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CROPS_DIR = DATA_DIR / "processed" / "satellite" / "crops"
DEMO_CACHE_DIR = DATA_DIR / "demo_cache"

# Curated reference cyclones
TARGET_STORMS = [
    {
        "name": "AMPHAN",
        "sid": "2020136N10088",
        "year": 2020,
        "crop": "AMPHAN_20200519_2358_MULTICHANNEL.h5",
        "sensor": "INSAT-3DR",
        "basin": "Bay of Bengal (BB)",
    },
    {
        "name": "BIPARJOY",
        "sid": "2023156N10067",
        "year": 2023,
        "crop": "BIPARJOY_20230612_2358_MULTICHANNEL.h5",
        "sensor": "INSAT-3DR",
        "basin": "Arabian Sea (AS)",
    },
    {
        "name": "REMAL",
        "sid": "2024145N14087",
        "year": 2024,
        "crop": "REMAL_20240526_1802_MULTICHANNEL.h5",
        "sensor": "INSAT-3DR",
        "basin": "Bay of Bengal (BB)",
    },
    {
        "name": "DANA",
        "sid": "2024295N15092",
        "year": 2024,
        "crop": "DANA_20241025_2330_MULTICHANNEL.h5",
        "sensor": "INSAT-3DS",
        "basin": "Bay of Bengal (BB)",
    },
    {
        "name": "MOCHA",
        "sid": "2023129N08091",
        "year": 2023,
        "crop": None,
        "sensor": "INSAT-3DR",
        "basin": "Bay of Bengal (BB)",
    },
    {
        "name": "TAUKTAE",
        "sid": "2021133N10071",
        "year": 2021,
        "crop": None,
        "sensor": "INSAT-3D",
        "basin": "Arabian Sea (AS)",
    },
    {
        "name": "YAAS",
        "sid": "2021143N15090",
        "year": 2021,
        "crop": None,
        "sensor": "INSAT-3D",
        "basin": "Bay of Bengal (BB)",
    },
    {
        "name": "FANI",
        "sid": "2019116N02090",
        "year": 2019,
        "crop": None,
        "sensor": "INSAT-3D",
        "basin": "Bay of Bengal (BB)",
    },
    {
        "name": "FENGAL",
        "sid": "2024329N04089",
        "year": 2024,
        "crop": None,
        "sensor": "INSAT-3DS",
        "basin": "Bay of Bengal (BB)",
    },
]

STORM_REGISTRY: dict[str, dict[str, Any]] = {}


def populate_initial_registry():
    """Build fast in-memory directory for satellite crops."""
    for item in TARGET_STORMS:
        name = item["name"]
        crop_file = CROPS_DIR / item["crop"] if item["crop"] else None
        has_crop = crop_file is not None and crop_file.is_file()

        STORM_REGISTRY[name] = {
            "storm_id": item["sid"],
            "canonical_name": name,
            "season_year": item["year"],
            "primary_basin": item["basin"],
            "has_satellite_crop": has_crop,
            "crop_filename": item["crop"] if has_crop else None,
            "satellite_sensor": item["sensor"],
        }


populate_initial_registry()


class CycloneService:
    """Encapsulates storm queries, track extraction, and offline cache fallbacks."""

    @staticmethod
    def list_storms(
        search: str | None = None,
        basin: str | None = None,
        season_year: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return storms from PostgreSQL vayumarg database with canonical SID and compatibility alias."""
        try:
            with get_db_session() as session:
                stmt = select(Storm, StormAlias.agency_storm_id).join(
                    StormAlias,
                    (StormAlias.storm_id == Storm.id) & (StormAlias.source_agency == "IBTRACS"),
                    isouter=True,
                )

                if search:
                    s_pat = f"%{search.strip()}%"
                    stmt = stmt.where(
                        (Storm.canonical_name.ilike(s_pat))
                        | (StormAlias.agency_storm_id.ilike(s_pat))
                    )

                if basin:
                    stmt = stmt.where(Storm.primary_basin == basin.upper())

                if season_year:
                    stmt = stmt.where(Storm.season_year == season_year)

                stmt = stmt.order_by(Storm.season_year.desc(), Storm.canonical_name).limit(limit)
                rows = session.execute(stmt).all()

                results = []
                for storm, sid in rows:
                    resolved_sid = sid or str(storm.id)
                    results.append(
                        {
                            "storm_id": str(storm.id),
                            "canonical_sid": resolved_sid,
                            "storm_sid": resolved_sid,
                            "canonical_name": storm.canonical_name,
                            "season_year": storm.season_year,
                            "primary_basin": storm.primary_basin,
                            "nature": storm.nature,
                        }
                    )
                return results
        except Exception:
            # Fallback to local target storms if DB is unavailable
            return [
                {
                    "storm_id": item["sid"],
                    "canonical_sid": item["sid"],
                    "storm_sid": item["sid"],
                    "canonical_name": item["name"],
                    "season_year": item["year"],
                    "primary_basin": item["basin"],
                    "nature": "TS",
                }
                for item in TARGET_STORMS
            ]

    @staticmethod
    def get_storm(storm_identifier: str) -> dict[str, Any]:
        """Retrieve full storm details by canonical SID, name, or UUID with automatic cache fallback."""
        clean_name = storm_identifier.strip().upper()
        cache_prof: Path | None = None
        cache_track: Path | None = None
        for p_file in (DEMO_CACHE_DIR / "storms").glob("*_profile.json"):
            if clean_name in p_file.name.upper():
                cache_prof = p_file
                t_candidate = p_file.parent / p_file.name.replace("_profile.json", "_track.json")
                if t_candidate.is_file():
                    cache_track = t_candidate
                break

        try:
            with get_db_session() as session:
                storm, sid = resolve_storm_in_database(session, storm_identifier)

                aliases = (
                    session.execute(select(StormAlias).where(StormAlias.storm_id == storm.id))
                    .scalars()
                    .all()
                )

                agency_counts = session.execute(
                    select(TrackObservation.source_agency, func.count(TrackObservation.id))
                    .where(TrackObservation.storm_id == storm.id)
                    .group_by(TrackObservation.source_agency)
                ).all()

                min_t, max_t = session.execute(
                    select(
                        func.min(TrackObservation.observation_time_utc),
                        func.max(TrackObservation.observation_time_utc),
                    ).where(TrackObservation.storm_id == storm.id)
                ).one()

                raw_obs = (
                    session.execute(
                        select(TrackObservation)
                        .where(TrackObservation.storm_id == storm.id)
                        .order_by(TrackObservation.observation_time_utc)
                    )
                    .scalars()
                    .all()
                )
                clean_obs = validate_and_clean_observations(
                    list(raw_obs), datetime(2100, 1, 1, tzinfo=UTC)
                )

                prof = {
                    "storm_id": str(storm.id),
                    "canonical_sid": sid,
                    "storm_sid": sid,
                    "canonical_name": storm.canonical_name,
                    "season_year": storm.season_year,
                    "primary_basin": storm.primary_basin,
                    "nature": storm.nature,
                    "start_time_utc": min_t.isoformat() if min_t else None,
                    "end_time_utc": max_t.isoformat() if max_t else None,
                    "total_observations": sum(c for _, c in agency_counts),
                    "agencies_available": dict(agency_counts),
                    "aliases": [
                        {
                            "source_agency": a.source_agency,
                            "agency_storm_id": a.agency_storm_id,
                            "agency_storm_name": a.agency_storm_name,
                        }
                        for a in aliases
                    ],
                }
                return {
                    "profile": prof,
                    "observations": [p.model_dump() for p in clean_obs],
                    **prof,
                }
        except Exception:
            if cache_prof and cache_prof.is_file():
                with open(cache_prof, encoding="utf-8") as f:
                    prof_data = json.load(f)
                track_data = []
                if cache_track and cache_track.is_file():
                    with open(cache_track, encoding="utf-8") as f:
                        track_data = json.load(f)
                if "canonical_sid" not in prof_data:
                    prof_data["canonical_sid"] = prof_data.get("storm_id", clean_name)
                if "storm_sid" not in prof_data:
                    prof_data["storm_sid"] = prof_data["canonical_sid"]
                return {
                    "profile": prof_data,
                    "observations": track_data,
                    **prof_data,
                }
            for t in TARGET_STORMS:
                if t["name"].upper() == clean_name or t["sid"].upper() == clean_name:
                    prof_data = {
                        "storm_id": t["sid"],
                        "canonical_sid": t["sid"],
                        "storm_sid": t["sid"],
                        "canonical_name": t["name"],
                        "season_year": t["year"],
                        "primary_basin": t["basin"],
                        "nature": "TS",
                    }
                    return {"profile": prof_data, "observations": [], **prof_data}
            raise KeyError(f"Storm '{storm_identifier}' not found.") from None

    @staticmethod
    def get_storm_track(
        storm_identifier: str,
        agency: str = "IMD",
        up_to_time_utc: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve agency-specific historical track with GeoJSON geometry."""
        clean_name = storm_identifier.strip().upper()
        cache_track: Path | None = None
        for p_file in (DEMO_CACHE_DIR / "storms").glob("*_track.json"):
            if clean_name in p_file.name.upper():
                cache_track = p_file
                break

        try:
            with get_db_session() as session:
                storm, sid = resolve_storm_in_database(session, storm_identifier)

                stmt = select(TrackObservation).where(
                    TrackObservation.storm_id == storm.id,
                    TrackObservation.source_agency == agency.upper(),
                )

                cutoff_dt: datetime | None = None
                if up_to_time_utc:
                    cutoff_dt = datetime.fromisoformat(up_to_time_utc.replace("Z", "+00:00"))
                    if cutoff_dt.tzinfo is None:
                        cutoff_dt = cutoff_dt.replace(tzinfo=UTC)
                    stmt = stmt.where(TrackObservation.observation_time_utc <= cutoff_dt)

                stmt = stmt.order_by(TrackObservation.observation_time_utc)
                raw_obs = session.execute(stmt).scalars().all()

                clean_obs = validate_and_clean_observations(
                    list(raw_obs),
                    cutoff_dt or datetime(2100, 1, 1, tzinfo=UTC),
                )

                features = []
                coords = []
                for p in clean_obs:
                    coords.append([p.longitude, p.latitude])
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
                            "properties": {
                                "observation_time_utc": p.observation_time_utc.isoformat(),
                                "latitude": p.latitude,
                                "longitude": p.longitude,
                                "wind_speed_knots": p.wind_speed_knots,
                                "central_pressure_hpa": p.central_pressure_hpa,
                                "averaging_period": p.averaging_period,
                                "imd_category": p.imd_category,
                                "source_record_id": p.source_record_id,
                                "stage": "HISTORICAL_INPUT",
                            },
                        }
                    )

                if len(coords) >= 2:
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": coords},
                            "properties": {
                                "stage": "HISTORICAL_TRACK_LINE",
                                "agency": agency.upper(),
                                "observation_count": len(coords),
                            },
                        }
                    )

                return {
                    "storm_id": str(storm.id),
                    "canonical_sid": sid,
                    "storm_sid": sid,
                    "canonical_name": storm.canonical_name,
                    "source_agency": agency.upper(),
                    "observation_count": len(clean_obs),
                    "observations": [p.model_dump() for p in clean_obs],
                    "geojson": {"type": "FeatureCollection", "features": features},
                }
        except Exception:
            if cache_track and cache_track.is_file():
                with open(cache_track, encoding="utf-8") as f:
                    track_data = json.load(f)
                features = []
                coords = []
                for p in track_data:
                    lat = p.get("latitude")
                    lon = p.get("longitude")
                    if lat is not None and lon is not None:
                        coords.append([lon, lat])
                        features.append(
                            {
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                                "properties": p,
                            }
                        )
                if len(coords) >= 2:
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": coords},
                            "properties": {
                                "stage": "HISTORICAL_TRACK_LINE",
                                "agency": agency.upper(),
                                "observation_count": len(coords),
                            },
                        }
                    )
                return {
                    "storm_id": clean_name,
                    "canonical_sid": clean_name,
                    "storm_sid": clean_name,
                    "canonical_name": clean_name,
                    "source_agency": agency.upper(),
                    "observation_count": len(track_data),
                    "observations": track_data,
                    "geojson": {"type": "FeatureCollection", "features": features},
                }
            raise KeyError(f"Track for storm '{storm_identifier}' not found.") from None

