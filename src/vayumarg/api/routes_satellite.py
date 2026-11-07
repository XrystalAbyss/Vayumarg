"""FastAPI Router for Module A Authentic Satellite Intelligence Subsystem.

Exposes verified INSAT satellite crops, real image previews (PNG/WebP),
quantitative image analytics, sensor calibration parameters, official IMD/JTWC
historical track associations, and task-specific model eligibility flags.
"""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from vayumarg.satellite.provenance import (
    AUTHENTIC_SATELLITE_REGISTRY,
    GroundTruthObservation,
    ProvenanceRecord,
)
from vayumarg.satellite.service import get_satellite_service
from vayumarg.satellite.visualizer import (
    COLORMAP_SPECS,
    ColormapType,
    SatelliteVisualizer,
)

router = APIRouter(prefix="/api/v1/satellite", tags=["Authentic Satellite Intelligence"])


# Response Models
class CropListItem(BaseModel):
    crop_id: str
    storm_name: str
    canonical_storm_sid: str
    season_year: int
    ocean_basin: str
    satellite: str
    sensor: str
    product_code: str
    crop_filename: str
    crop_sha256: str
    verification_status: str
    acquisition_start_utc: str
    estimated_local_scan_time_utc: str
    scan_time_uncertainty: str
    extent_km: float
    target_grid_spacing_km: float
    center_latitude: float
    center_longitude: float
    available_channels: list[str]
    primary_imd_eligible: bool
    dana_ineligibility_notice: str | None


class CurrentStateLabelsResponse(BaseModel):
    storm_name: str
    canonical_storm_sid: str
    acquisition_time_utc: str
    primary_imd_eligible: bool
    dana_ineligibility_notice: str | None
    primary_imd_observation: GroundTruthObservation | None
    secondary_jtwc_observation: GroundTruthObservation | None
    temporal_offset_minutes: float
    spatial_offset_km: float
    model_eligibility: dict[str, bool]


class LegendTickModel(BaseModel):
    kelvin: float
    celsius: float
    hex_color: str
    description: str


class ColormapLegendResponse(BaseModel):
    name: str
    display_name: str
    channel_affinity: str
    temp_min_k: float
    temp_max_k: float
    scientific_description: str
    ticks: list[LegendTickModel]


class SubsystemHealthResponse(BaseModel):
    status: str
    verified_crops_count: int
    authentic_storms: list[str]
    supported_channels: list[str]
    supported_colormaps: list[str]
    governance_status: str


@router.get("/health", response_model=SubsystemHealthResponse)
def get_subsystem_health() -> SubsystemHealthResponse:
    """Check health and integrity of Module A Authentic Satellite Subsystem."""
    service = get_satellite_service()
    crops = service.list_authentic_crops()
    return SubsystemHealthResponse(
        status="HEALTHY",
        verified_crops_count=len(crops),
        authentic_storms=[c.storm_name for c in crops],
        supported_channels=["TIR-1", "WV", "TIR-2", "MIR"],
        supported_colormaps=list(COLORMAP_SPECS.keys()),
        governance_status="REAL_VERIFIED",
    )


@router.get("/crops", response_model=list[CropListItem])
def list_crops() -> list[CropListItem]:
    """List all authentic real-verified satellite crops with summary metadata."""
    service = get_satellite_service()
    crops = service.list_authentic_crops()
    return [
        CropListItem(
            crop_id=c.crop_id,
            storm_name=c.storm_name,
            canonical_storm_sid=c.canonical_storm_sid,
            season_year=c.season_year,
            ocean_basin=c.ocean_basin,
            satellite=c.satellite,
            sensor=c.sensor,
            product_code=c.product_code,
            crop_filename=c.crop_filename,
            crop_sha256=c.crop_sha256,
            verification_status=c.verification_status,
            acquisition_start_utc=c.acquisition_start_utc,
            estimated_local_scan_time_utc=c.estimated_local_scan_time_utc,
            scan_time_uncertainty=c.scan_time_uncertainty,
            extent_km=c.extent_km,
            target_grid_spacing_km=c.target_grid_spacing_km,
            center_latitude=c.center_latitude,
            center_longitude=c.center_longitude,
            available_channels=c.available_channels,
            primary_imd_eligible=c.primary_imd_eligible,
            dana_ineligibility_notice=c.dana_ineligibility_notice,
        )
        for c in crops
    ]


@router.get("/crops/{storm_or_id}", response_model=ProvenanceRecord)
def get_crop_metadata(storm_or_id: str) -> ProvenanceRecord:
    """Retrieve full scientific metadata, calibration parameters, and lineage for a crop."""
    service = get_satellite_service()
    try:
        return service.get_crop_provenance(storm_or_id)
    except KeyError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Authentic satellite crop not found: '{storm_or_id}'. "
            f"Available authentic storms: {list(AUTHENTIC_SATELLITE_REGISTRY.keys())}",
        ) from err


@router.get("/crops/{storm_or_id}/labels", response_model=CurrentStateLabelsResponse)
def get_current_state_labels(storm_or_id: str) -> CurrentStateLabelsResponse:
    """Retrieve official historical ground-truth track association and eligibility."""
    service = get_satellite_service()
    try:
        record = service.get_crop_provenance(storm_or_id)
    except KeyError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Authentic satellite crop not found: '{storm_or_id}'",
        ) from err

    return CurrentStateLabelsResponse(
        storm_name=record.storm_name,
        canonical_storm_sid=record.canonical_storm_sid,
        acquisition_time_utc=record.acquisition_start_utc,
        primary_imd_eligible=record.primary_imd_eligible,
        dana_ineligibility_notice=record.dana_ineligibility_notice,
        primary_imd_observation=record.primary_imd_observation,
        secondary_jtwc_observation=record.secondary_jtwc_observation,
        temporal_offset_minutes=record.temporal_offset_minutes,
        spatial_offset_km=record.spatial_offset_km,
        model_eligibility=record.model_eligibility,
    )


@router.get("/crops/{storm_or_id}/channels/{channel}")
def get_channel_analytics(
    storm_or_id: str,
    channel: str,
) -> dict[str, Any]:
    """Retrieve comprehensive quantitative image analytics for a specific channel."""
    service = get_satellite_service()
    try:
        analytics = service.get_channel_analytics(storm_or_id, channel)
        return analytics.to_dict()
    except KeyError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Authentic satellite crop not found: '{storm_or_id}'",
        ) from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except FileNotFoundError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@router.get("/crops/{storm_or_id}/channels/{channel}/preview")
def get_channel_preview(
    storm_or_id: str,
    channel: str,
    colormap: ColormapType = Query(
        "thermal_ir",
        description="Scientific colormap: thermal_ir, grayscale_inv, dvorak_bd, water_vapor",
    ),
    format: Literal["png", "webp"] = Query(
        "png",
        description="Image output format: png or webp",
    ),
    include_legend: bool = Query(
        False,
        description="Whether to render an integrated composite card with title and Kelvin scale bar",
    ),
    highlight_clamped: bool = Query(
        False,
        description="Whether to highlight lower LUT clamped pixels in bright magenta",
    ),
) -> Response:
    """Return fast cached scientific image preview (PNG/WebP) for channel switching."""
    service = get_satellite_service()
    try:
        preview_bytes = service.get_channel_preview(
            storm_or_id=storm_or_id,
            channel=channel,
            colormap=colormap,
            output_format=format.upper(),  # type: ignore
            include_legend=include_legend,
            highlight_clamped=highlight_clamped,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Authentic satellite crop not found: '{storm_or_id}'",
        ) from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except FileNotFoundError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err

    media_type = "image/webp" if format.lower() == "webp" else "image/png"
    return Response(
        content=preview_bytes,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "X-Scientific-Source": "REAL_VERIFIED_INSAT",
        },
    )


@router.get("/legends/{colormap}", response_model=ColormapLegendResponse)
def get_colormap_legend_metadata(colormap: ColormapType) -> ColormapLegendResponse:
    """Get quantitative tick marks and physical temperature bounds for a colormap."""
    if colormap not in COLORMAP_SPECS:
        raise HTTPException(
            status_code=404,
            detail=f"Colormap '{colormap}' not found. Supported: {list(COLORMAP_SPECS.keys())}",
        )
    spec = COLORMAP_SPECS[colormap]
    return ColormapLegendResponse(
        name=spec.name,
        display_name=spec.display_name,
        channel_affinity=spec.channel_affinity,
        temp_min_k=spec.temp_min_k,
        temp_max_k=spec.temp_max_k,
        scientific_description=spec.scientific_description,
        ticks=[
            LegendTickModel(
                kelvin=t.kelvin,
                celsius=t.celsius,
                hex_color=t.hex_color,
                description=t.description,
            )
            for t in spec.ticks
        ],
    )


@router.get("/legends/{colormap}/image")
def get_colormap_legend_image(
    colormap: ColormapType,
    width: int = Query(450, ge=200, le=1200),
    height: int = Query(65, ge=40, le=200),
) -> Response:
    """Render a standalone scientific measurement colorbar legend with Kelvin scale."""
    if colormap not in COLORMAP_SPECS:
        raise HTTPException(
            status_code=404,
            detail=f"Colormap '{colormap}' not found. Supported: {list(COLORMAP_SPECS.keys())}",
        )

    legend_img = SatelliteVisualizer.render_colorbar_legend(
        colormap=colormap,
        width=width,
        height=height,
    )
    import io

    buf = io.BytesIO()
    legend_img.save(buf, format="PNG", optimize=True)
    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400, immutable"},
    )
