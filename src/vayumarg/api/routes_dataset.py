"""FastAPI Router for Authentic Satellite Dataset Explorer & Scientific Image Gallery.

Serves verified ISRO MOSDAC INSAT-3DR/3DS multichannel crops, full physical analytics,
pixel inspection, side-by-side comparison metadata, and immutable offline dataset exports.
"""

import csv
import io
import json
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Response

from vayumarg.core.config import settings
from vayumarg.satellite.provenance import (
    AUTHENTIC_SATELLITE_REGISTRY,
    get_provenance_by_identifier,
)
from vayumarg.satellite.service import get_satellite_service
from vayumarg.satellite.visualizer import (
    ColormapType,
)

router = APIRouter(prefix="/api/dataset", tags=["Satellite Dataset Explorer"])

PREVIEWS_DIR = Path(settings.DATA_DIR) / "processed" / "satellite" / "previews"


def _load_cached_channel_analytics(crop_sha: str, channel: str) -> dict[str, Any] | None:
    """Load precomputed channel analytics from disk cache if present."""
    slug = f"{crop_sha[:16]}_{channel}_analytics.json"
    p = PREVIEWS_DIR / slug
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


@router.get("/summary")
def get_dataset_summary() -> dict[str, Any]:
    """Return top-level inventory summary of authentic physical observations."""
    return {
        "physical_observations_count": len(AUTHENTIC_SATELLITE_REGISTRY),
        "calibrated_preview_variations_count": 88,
        "authentic_storms": list(AUTHENTIC_SATELLITE_REGISTRY.keys()),
        "sensor_platforms": ["INSAT-3DR", "INSAT-3DS"],
        "ocean_basins": ["Bay of Bengal (NI)", "Arabian Sea (NI)"],
        "supported_channels": ["TIR-1", "TIR-2", "WV", "MIR"],
        "supported_colormaps": ["thermal_ir", "grayscale_inv", "dvorak_bd", "water_vapor"],
        "verified_crops_status": "REAL_VERIFIED",
        "raw_archive_audit": {
            "unregistered_raw_hdf5": [
                {
                    "storm_name": "FANI",
                    "filename": "3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5",
                    "size_bytes": 303911822,
                    "status": "RAW_UNPROCESSED_SOURCE",
                    "note": "Complete raw MOSDAC HDF5 exists; no calibrated crop registered in pipeline.",
                },
                {
                    "storm_name": "TAUKTAE",
                    "filename": "3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5",
                    "size_bytes": 301621093,
                    "status": "RAW_UNPROCESSED_SOURCE",
                    "note": "Complete raw MOSDAC HDF5 exists; no calibrated crop registered in pipeline.",
                },
            ],
            "incomplete_downloads": [
                {
                    "storm_name": "FENGAL",
                    "filename": "3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5.part",
                    "size_bytes": 309133312,
                    "status": "PARTIAL_INCOMPLETE_DOWNLOAD",
                    "note": "Aborted MOSDAC acquisition (.part); invalid HDF5 header.",
                },
                {
                    "storm_name": "REMAL_PASS2",
                    "filename": "3RIMG_27MAY2024_1915_L1B_STD_V01R00.h5.part",
                    "size_bytes": 31457280,
                    "status": "PARTIAL_INCOMPLETE_DOWNLOAD",
                    "note": "Aborted acquisition (.part); excluded from verified study cohort.",
                },
            ],
        },
        "scientific_disclaimer": (
            "Four authentic physical satellite observations are available in this study. "
            "Preview variations (88 PNGs) represent physical colormap enhancements and overlays "
            "across 4 spectral channels, not independent training samples."
        ),
    }


@router.get("/samples")
def list_dataset_samples() -> list[dict[str, Any]]:
    """Return authoritative list of 4 authentic physical satellite samples with preview links and analytics."""
    get_satellite_service()
    samples: list[dict[str, Any]] = []

    for storm_name, record in AUTHENTIC_SATELLITE_REGISTRY.items():
        # Build preview URL map for available colormaps per channel
        previews: dict[str, dict[str, str]] = {}
        channel_summaries: dict[str, Any] = {}

        for ch in record.available_channels:
            previews[ch] = {}
            for cm in ["thermal_ir", "grayscale_inv", "dvorak_bd", "water_vapor"]:
                if cm == "water_vapor" and ch != "WV":
                    continue
                if cm == "dvorak_bd" and ch not in ("TIR-1", "TIR-2"):
                    continue
                previews[ch][cm] = f"/api/dataset/preview/{storm_name}/{ch}/{cm}"

            # Attach cached analytics summary
            cached_an = _load_cached_channel_analytics(record.crop_sha256, ch)
            if cached_an:
                channel_summaries[ch] = {
                    "min_tb_k": cached_an.get("min_tb_k"),
                    "min_non_clamped_tb_k": cached_an.get("min_non_clamped_tb_k"),
                    "max_tb_k": cached_an.get("max_tb_k"),
                    "mean_tb_k": cached_an.get("mean_tb_k"),
                    "clamped_fraction": cached_an.get("clamped_fraction", 0.0),
                    "valid_fraction": cached_an.get("valid_fraction", 1.0),
                    "cold_cloud_fractions": cached_an.get("cold_cloud_fractions", []),
                }

        sample_item = {
            "crop_id": record.crop_id,
            "storm_name": record.storm_name,
            "canonical_storm_sid": record.canonical_storm_sid,
            "season_year": record.season_year,
            "ocean_basin": record.ocean_basin,
            "satellite": record.satellite,
            "sensor": record.sensor,
            "product_code": record.product_code,
            "source_filename": record.source_filename,
            "source_sha256": record.source_sha256,
            "crop_filename": record.crop_filename,
            "crop_sha256": record.crop_sha256,
            "verification_status": record.verification_status,
            "acquisition_start_utc": record.acquisition_start_utc,
            "estimated_local_scan_time_utc": record.estimated_local_scan_time_utc,
            "scan_time_uncertainty": record.scan_time_uncertainty,
            "crop_extent_km": record.crop_extent_km,
            "target_grid_spacing_km": record.target_grid_spacing_km,
            "grid_dimensions": [201, 201],
            "total_pixels": 40401,
            "center_latitude": record.center_latitude,
            "center_longitude": record.center_longitude,
            "available_channels": record.available_channels,
            "channel_resolutions_km": record.channel_resolutions_km,
            "primary_imd_eligible": record.primary_imd_eligible,
            "primary_imd_observation": record.primary_imd_observation.__dict__
            if record.primary_imd_observation
            else None,
            "secondary_jtwc_observation": record.secondary_jtwc_observation.__dict__
            if record.secondary_jtwc_observation
            else None,
            "dana_ineligibility_notice": record.dana_ineligibility_notice,
            "exclusion_reason": record.exclusion_reason,
            "model_eligibility": record.model_eligibility,
            "preview_urls": previews,
            "channel_summaries": channel_summaries,
        }
        samples.append(sample_item)

    return samples


@router.get("/samples/{storm_or_id}")
def get_dataset_sample_detail(storm_or_id: str) -> dict[str, Any]:
    """Return full scientific sample detail including all channel analytics, radial profiles, and provenance."""
    record = get_provenance_by_identifier(storm_or_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Authentic satellite crop '{storm_or_id}' not found. Available: {list(AUTHENTIC_SATELLITE_REGISTRY.keys())}",
        )

    service = get_satellite_service()
    channels_data: dict[str, Any] = {}

    for ch in record.available_channels:
        # Check disk cache first, or compute
        an_data = _load_cached_channel_analytics(record.crop_sha256, ch)
        if not an_data:
            try:
                an_obj = service.get_channel_analytics(record.storm_name, ch)
                an_data = an_obj.to_dict()
            except Exception as err:
                an_data = {"error": str(err)}

        channels_data[ch] = {
            "channel_name": ch,
            "native_resolution_km": record.channel_resolutions_km.get(ch, 4.0),
            "delivered_resolution_km": record.target_grid_spacing_km,
            "analytics": an_data,
        }

    return {
        "record": record.to_dict(),
        "channels": channels_data,
        "grid": {
            "shape": [201, 201],
            "total_pixels": 40401,
            "extent_km": record.crop_extent_km,
            "spacing_km": record.target_grid_spacing_km,
            "center_coord": [record.center_latitude, record.center_longitude],
        },
        "scientific_integrity": {
            "source_sha256": record.source_sha256,
            "crop_sha256": record.crop_sha256,
            "verification_status": record.verification_status,
            "is_calibrated_insat_l1b": True,
            "dana_policy": record.dana_ineligibility_notice,
        },
    }


@router.get("/preview/{storm}/{channel}/{colormap}")
def get_dataset_preview_image(
    storm: str,
    channel: str,
    colormap: ColormapType,
    composite: bool = Query(
        False, description="Whether to include Kelvin measurement scale and header overlay"
    ),
    highlight_clamped: bool = Query(
        False, description="Highlight lower LUT clamped boundary pixels (<180K) in magenta"
    ),
    format: Literal["png", "webp"] = Query("png", description="Image format"),
) -> Response:
    """Serve pre-rendered or dynamically rendered authentic satellite preview PNG/WebP."""
    service = get_satellite_service()
    try:
        preview_bytes = service.get_channel_preview(
            storm_or_id=storm,
            channel=channel,
            colormap=colormap,
            output_format=format.upper(),  # type: ignore
            include_legend=composite,
            highlight_clamped=highlight_clamped,
        )
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Preview render error: {err}") from err

    media_type = "image/webp" if format.lower() == "webp" else "image/png"
    return Response(
        content=preview_bytes,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "X-Authentic-Observation": storm.upper(),
            "X-Spectral-Channel": channel.upper(),
            "X-Scientific-Colormap": colormap,
        },
    )


@router.get("/pixel")
def get_dataset_pixel_value(
    storm: str = Query(..., description="Storm name (REMAL, AMPHAN, BIPARJOY, DANA)"),
    channel: str = Query("TIR-1", description="Channel name: TIR-1, TIR-2, WV, MIR"),
    x: int = Query(..., ge=0, le=200, description="Column pixel coordinate (0-200)"),
    y: int = Query(..., ge=0, le=200, description="Row pixel coordinate (0-200)"),
) -> dict[str, Any]:
    """Retrieve exact physical brightness temperature and validation status for a pixel coordinate."""
    service = get_satellite_service()
    try:
        arr_k, valid_mask, clamped_mask = service.load_channel_array(storm, channel)
    except Exception as err:
        raise HTTPException(status_code=404, detail=str(err)) from err

    val_k = float(arr_k[y, x])
    is_valid = bool(valid_mask[y, x])
    is_clamped = bool(clamped_mask[y, x])

    # Distance from center pixel (100, 100) in km
    dx_px = x - 100
    dy_px = y - 100
    dist_km = round(((dx_px**2 + dy_px**2) ** 0.5) * 4.0, 1)

    return {
        "storm": storm.upper(),
        "channel": channel.upper(),
        "pixel_coord": {"x": x, "y": y},
        "distance_from_center_km": dist_km,
        "temperature_kelvin": round(val_k, 2) if is_valid else None,
        "temperature_celsius": round(val_k - 273.15, 2) if is_valid else None,
        "is_valid": is_valid,
        "is_lower_lut_clamped": is_clamped,
        "lut_boundary_k": 179.86,
    }


@router.get("/export/manifest.json")
def export_dataset_manifest() -> Response:
    """Export authoritative machine-readable JSON dataset manifest referencing immutable physical assets."""
    manifest = {
        "dataset_name": "VAYUMARG Authentic ISRO INSAT Multichannel Satellite Benchmark",
        "version": "1.0.0",
        "generation_timestamp_utc": "2026-11-03T00:00:00Z",
        "curation_authority": "Vayumarg Scientific Intelligence Team",
        "data_license": "Open Meteorological Research & Academic Benchmark",
        "source_agency": "ISRO MOSDAC Level 1B Standard Standardised Imager Granules",
        "ground_truth_agencies": [
            "India Meteorological Department (RSMC New Delhi)",
            "Joint Typhoon Warning Center (JTWC / US Navy)",
            "NOAA NCEI IBTrACS v04r01",
        ],
        "inventory": {
            "physical_observations_count": len(AUTHENTIC_SATELLITE_REGISTRY),
            "colormapped_preview_variants_count": 88,
            "channels_per_sample": 4,
            "crop_grid_dimensions": [201, 201],
            "crop_extent_km": 800.0,
            "grid_spacing_km": 4.0,
        },
        "samples": [],
    }

    for _storm_name, record in AUTHENTIC_SATELLITE_REGISTRY.items():
        manifest["samples"].append(
            {
                "crop_id": record.crop_id,
                "storm_name": record.storm_name,
                "canonical_storm_sid": record.canonical_storm_sid,
                "season_year": record.season_year,
                "ocean_basin": record.ocean_basin,
                "satellite": record.satellite,
                "sensor": record.sensor,
                "product_code": record.product_code,
                "source_granule": {
                    "filename": record.source_filename,
                    "sha256": record.source_sha256,
                },
                "processed_crop": {
                    "filename": record.crop_filename,
                    "sha256": record.crop_sha256,
                    "extent_km": record.crop_extent_km,
                    "spacing_km": record.target_grid_spacing_km,
                    "shape": [201, 201],
                },
                "acquisition": {
                    "nominal_start_utc": record.acquisition_start_utc,
                    "estimated_local_scan_utc": record.estimated_local_scan_time_utc,
                    "scan_time_uncertainty": record.scan_time_uncertainty,
                },
                "center_fix": {
                    "latitude": record.center_latitude,
                    "longitude": record.center_longitude,
                },
                "ground_truth_labels": {
                    "primary_imd": record.primary_imd_observation.__dict__
                    if record.primary_imd_observation
                    else None,
                    "secondary_jtwc": record.secondary_jtwc_observation.__dict__
                    if record.secondary_jtwc_observation
                    else None,
                    "primary_imd_eligible": record.primary_imd_eligible,
                    "dana_policy_note": record.dana_ineligibility_notice,
                    "exclusion_reason": record.exclusion_reason,
                },
                "available_channels": record.available_channels,
            }
        )

    content = json.dumps(manifest, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="vayumarg_satellite_manifest.json"'},
    )


@router.get("/export/metadata.csv")
def export_dataset_metadata_csv() -> Response:
    """Export authoritative CSV summary of authentic observations and scientific metadata."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    # Header
    writer.writerow(
        [
            "crop_id",
            "storm_name",
            "canonical_sid",
            "season_year",
            "ocean_basin",
            "satellite",
            "sensor",
            "acquisition_start_utc",
            "estimated_local_scan_utc",
            "center_lat",
            "center_lon",
            "extent_km",
            "grid_spacing_km",
            "source_filename",
            "source_sha256",
            "crop_filename",
            "crop_sha256",
            "primary_imd_eligible",
            "imd_category",
            "imd_wind_knots_3min",
            "imd_pressure_hpa",
            "jtwc_category",
            "jtwc_wind_knots_1min",
            "dana_policy_note",
            "verification_status",
        ]
    )

    for _storm_name, record in AUTHENTIC_SATELLITE_REGISTRY.items():
        imd = record.primary_imd_observation
        jtwc = record.secondary_jtwc_observation
        writer.writerow(
            [
                record.crop_id,
                record.storm_name,
                record.canonical_storm_sid,
                record.season_year,
                record.ocean_basin,
                record.satellite,
                record.sensor,
                record.acquisition_start_utc,
                record.estimated_local_scan_time_utc,
                record.center_latitude,
                record.center_longitude,
                record.crop_extent_km,
                record.target_grid_spacing_km,
                record.source_filename,
                record.source_sha256,
                record.crop_filename,
                record.crop_sha256,
                record.primary_imd_eligible,
                imd.cyclone_category if imd else "INELIGIBLE",
                imd.wind_speed_knots if imd else "",
                imd.central_pressure_hpa if imd else "",
                jtwc.cyclone_category if jtwc else "",
                jtwc.wind_speed_knots if jtwc else "",
                record.dana_ineligibility_notice or "",
                record.verification_status,
            ]
        )

    content = buf.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="vayumarg_satellite_metadata.csv"'},
    )
