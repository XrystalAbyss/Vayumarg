"""Multispectral satellite crop retrieval, PNG image rendering, and brightness temperature analytics routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from vayumarg.services.satellite_service import SatelliteService

router = APIRouter(tags=["Satellite Intelligence (Module A)"])


@router.get("/api/satellite/crops")
def list_satellite_crops() -> list[dict[str, Any]]:
    """List all authentic multi-channel INSAT crops available on disk."""
    return SatelliteService.list_crops()


@router.get("/api/satellite/crop/{storm_name}/image")
@router.get("/api/satellite/crops/{storm_name}/preview")
def get_satellite_image(
    storm_name: str,
    channel: str = Query("TIR-1", description="Satellite spectral channel: TIR-1, TIR-2, WV, MIR"),
) -> Response:
    """Render authentic HDF5 crop channel as PNG image bytes directly using physical BD-Curve Kelvin colormap."""
    try:
        png_bytes = SatelliteService.render_crop_image(storm_name=storm_name, channel=channel)
        return Response(content=png_bytes, media_type="image/png")
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"No satellite crop registered for '{storm_name}'"
        ) from exc
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf)) from fnf
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render satellite crop: {e}") from e


@router.get("/api/satellite/crop/{storm_name}/metrics")
@router.get("/api/satellite/crops/{storm_name}/metrics")
def get_satellite_metrics(
    storm_name: str,
    channel: str = Query("TIR-1", description="Spectral channel for physical feature calculation"),
) -> dict[str, Any]:
    """Compute physical brightness-temperature features and cold-cloud fractions from authentic HDF5 crop."""
    try:
        return SatelliteService.compute_metrics(storm_name=storm_name, channel=channel)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"No satellite crop registered for '{storm_name}'"
        ) from exc
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf)) from fnf
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute physical crop metrics: {e}"
        ) from e

