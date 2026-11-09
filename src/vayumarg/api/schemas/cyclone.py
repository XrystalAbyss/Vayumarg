"""Schemas for cyclone metadata, historical observations, and tracking."""

from typing import Any

from pydantic import BaseModel, Field


class StormSummary(BaseModel):
    """Summary of a cyclone in the catalog."""

    storm_id: str = Field(description="Surrogate database UUID or storm identifier")
    canonical_sid: str = Field(description="Authoritative IBTrACS SID (e.g. 2023156N10067)")
    storm_sid: str | None = Field(
        default=None,
        description="Compatibility alias pointing to canonical_sid",
    )
    canonical_name: str = Field(description="Canonical storm name")
    season_year: int = Field(description="Year of season formation")
    primary_basin: str = Field(description="Basin code (e.g. AS, BB, NI)")
    nature: str = Field(default="TS", description="Cyclone nature/type code")


class StormAliasSchema(BaseModel):
    """External agency alias for a cyclone."""

    source_agency: str
    agency_storm_id: str
    agency_storm_name: str | None = None


class StormProfile(BaseModel):
    """Comprehensive meteorological and operational profile for a storm."""

    storm_id: str
    canonical_sid: str
    storm_sid: str | None = None
    canonical_name: str
    season_year: int
    primary_basin: str
    nature: str
    start_time_utc: str | None = None
    end_time_utc: str | None = None
    total_observations: int = 0
    agencies_available: dict[str, int] = Field(default_factory=dict)
    aliases: list[StormAliasSchema] = Field(default_factory=list)


class TrackResponse(BaseModel):
    """Agency-specific historical track with GeoJSON geometry."""

    storm_id: str
    canonical_sid: str
    storm_sid: str | None = None
    canonical_name: str
    source_agency: str
    observation_count: int
    observations: list[dict[str, Any]]
    geojson: dict[str, Any]

