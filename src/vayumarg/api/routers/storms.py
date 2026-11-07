"""Cyclone catalog, storm metadata, and historical trajectory tracking routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from vayumarg.services.cyclone_service import STORM_REGISTRY, TARGET_STORMS, CycloneService

router = APIRouter(tags=["Cyclone Catalog & Tracking"])


@router.get("/api/storms")
def list_storms(
    search: str | None = Query(default=None, description="Search storm by canonical name or SID"),
    basin: str | None = Query(default=None, description="Filter by basin (e.g. NI, BB, AS)"),
    season_year: int | None = Query(default=None, description="Filter by season year"),
    limit: int = Query(default=100, ge=1, le=2000, description="Max storms to return"),
) -> list[dict[str, Any]]:
    """Return storms from PostgreSQL vayumarg database with canonical SID and metadata."""
    return CycloneService.list_storms(search=search, basin=basin, season_year=season_year, limit=limit)


@router.get("/api/storms/{storm_identifier}")
def get_storm(storm_identifier: str) -> dict[str, Any]:
    """Retrieve full storm details by canonical SID, name, or UUID with automatic cache fallback."""
    try:
        return CycloneService.get_storm(storm_identifier)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"Storm '{storm_identifier}' not found."
        ) from exc


@router.get("/api/storms/{storm_identifier}/track")
def get_storm_track(
    storm_identifier: str,
    agency: str = Query(
        default="IMD", description="Source agency: IMD (3-min), JTWC (1-min), or IBTRACS"
    ),
    up_to_time_utc: str | None = Query(
        default=None, description="Optional ISO 8601 UTC cutoff timestamp (LEAKAGE SHIELD)"
    ),
) -> dict[str, Any]:
    """Retrieve agency-specific historical track with GeoJSON geometry and coordinate sequences."""
    try:
        return CycloneService.get_storm_track(
            storm_identifier=storm_identifier,
            agency=agency,
            up_to_time_utc=up_to_time_utc,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"Track for storm '{storm_identifier}' not found."
        ) from exc


@router.get("/api/storms/{storm_identifier}/satellite")
def get_storm_satellite(storm_identifier: str) -> dict[str, Any]:
    """Retrieve satellite crop metadata for a specific storm."""
    clean_name = storm_identifier.strip().upper()
    reg = STORM_REGISTRY.get(clean_name)
    if not reg:
        for t in TARGET_STORMS:
            if t["name"].upper() == clean_name or t["sid"].upper() == clean_name:
                reg = {
                    "storm_id": t["sid"],
                    "canonical_name": t["name"],
                    "satellite_sensor": t["sensor"],
                    "crop_filename": t["crop"],
                }
                break
    if not reg or not reg.get("crop_filename"):
        raise HTTPException(
            status_code=404, detail=f"No satellite crop registered for '{storm_identifier}'"
        ) from None

    return {
        "storm_name": reg.get("canonical_name", clean_name),
        "satellite_platform": reg.get("satellite_sensor", "INSAT-3DR"),
        "crop_filename": reg.get("crop_filename"),
        "has_satellite_crop": True,
    }

