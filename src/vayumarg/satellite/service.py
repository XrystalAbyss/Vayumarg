"""Satellite Image Service for Module A Authentic Satellite Intelligence.

Loads verified INSAT HDF5 crops, computes physical observations and quantitative
metrics, produces scientific visual previews with Kelvin scale legends, and manages
an offline/disk preview cache for responsive channel switching.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import h5py
import numpy as np

from vayumarg.core.config import settings
from vayumarg.core.logging import get_logger
from vayumarg.satellite.analytics import ChannelAnalytics, SatelliteImageAnalyticsEngine
from vayumarg.satellite.provenance import (
    AUTHENTIC_SATELLITE_REGISTRY,
    ProvenanceRecord,
    get_provenance_by_identifier,
)
from vayumarg.satellite.visualizer import (
    ColormapType,
    SatelliteVisualizer,
)

logger = get_logger("vayumarg.satellite.service")


@dataclass
class ChannelDetail:
    """Detailed channel information and available analytics."""

    channel_name: str
    native_resolution_km: float
    delivered_resolution_km: float
    effective_resolution_km: float
    resampling_method: str
    units: str
    grid_shape: tuple[int, int]
    analytics: ChannelAnalytics


@dataclass
class CropSummary:
    """High-level summary of an authentic satellite crop."""

    crop_id: str
    storm_name: str
    canonical_storm_sid: str
    season_year: int
    ocean_basin: str
    satellite: str
    sensor: str
    product_code: str
    source_filename: str
    source_sha256: str
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


class SatelliteImageService:
    """Core service for managing authentic satellite crops, visualizations, and analytics."""

    def __init__(
        self,
        crops_dir: Path | str | None = None,
        cache_dir: Path | str | None = None,
    ):
        data_path = Path(settings.DATA_DIR)
        self.crops_dir = (
            Path(crops_dir) if crops_dir else (data_path / "processed" / "satellite" / "crops")
        )
        self.cache_dir = (
            Path(cache_dir) if cache_dir else (data_path / "processed" / "satellite" / "previews")
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, bytes] = {}

    def list_authentic_crops(self) -> list[CropSummary]:
        """List all verified authentic satellite crops."""
        summaries: list[CropSummary] = []
        for _storm_name, record in AUTHENTIC_SATELLITE_REGISTRY.items():
            summaries.append(
                CropSummary(
                    crop_id=record.crop_id,
                    storm_name=record.storm_name,
                    canonical_storm_sid=record.canonical_storm_sid,
                    season_year=record.season_year,
                    ocean_basin=record.ocean_basin,
                    satellite=record.satellite,
                    sensor=record.sensor,
                    product_code=record.product_code,
                    source_filename=record.source_filename,
                    source_sha256=record.source_sha256,
                    crop_filename=record.crop_filename,
                    crop_sha256=record.crop_sha256,
                    verification_status=record.verification_status,
                    acquisition_start_utc=record.acquisition_start_utc,
                    estimated_local_scan_time_utc=record.estimated_local_scan_time_utc,
                    scan_time_uncertainty=record.scan_time_uncertainty,
                    extent_km=record.crop_extent_km,
                    target_grid_spacing_km=record.target_grid_spacing_km,
                    center_latitude=record.center_latitude,
                    center_longitude=record.center_longitude,
                    available_channels=record.available_channels,
                    primary_imd_eligible=record.primary_imd_eligible,
                    dana_ineligibility_notice=record.dana_ineligibility_notice,
                )
            )
        return summaries

    def get_crop_provenance(self, storm_or_id: str) -> ProvenanceRecord:
        """Get authoritative provenance record by storm name or crop ID."""
        record = get_provenance_by_identifier(storm_or_id)
        if not record:
            raise KeyError(f"Authentic satellite crop not found: {storm_or_id}")
        return record

    def load_channel_array(
        self,
        storm_or_id: str,
        channel: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Load physical Kelvin array, valid mask, and clamped mask for a channel."""
        record = self.get_crop_provenance(storm_or_id)
        crop_file = self.crops_dir / record.crop_filename
        if not crop_file.is_file():
            raise FileNotFoundError(f"Processed crop file not found on disk: {crop_file}")

        ch_key = channel.upper().replace("_", "-")
        valid_chans = {c.upper().replace("_", "-"): c for c in record.available_channels}
        if ch_key not in valid_chans:
            raise ValueError(
                f"Channel '{channel}' unavailable for {record.storm_name}. "
                f"Available channels: {record.available_channels}"
            )
        actual_ch = valid_chans[ch_key]

        with h5py.File(crop_file, "r") as h5:
            # 1. Physical Kelvin array (coregistered)
            if "coregistered" in h5 and actual_ch in h5["coregistered"]:
                temps_k = h5["coregistered"][actual_ch][:].astype(float)
            else:
                raise KeyError(
                    f"Channel {actual_ch} not present in coregistered group of {crop_file.name}"
                )

            # 2. Combined valid mask from masks group
            if "masks" in h5 and "combined_valid_mask" in h5["masks"]:
                combined_mask = h5["masks"]["combined_valid_mask"][:].astype(bool)
            else:
                combined_mask = ~np.isnan(temps_k)

            # 3. Channel-specific valid & clamped masks from native group if available
            if "native" in h5 and actual_ch in h5["native"]:
                nat_grp = h5["native"][actual_ch]
                nat_valid = (
                    nat_grp["valid_mask"][:].astype(bool) if "valid_mask" in nat_grp else None
                )
                nat_clamped = (
                    nat_grp["clamped_mask"][:].astype(bool) if "clamped_mask" in nat_grp else None
                )
            else:
                nat_valid = None
                nat_clamped = None

            # For 201x201 channels (TIR-1, TIR-2, MIR, and INSAT-3DS WV), native valid mask matches coregistered shape
            if nat_valid is not None and nat_valid.shape == temps_k.shape:
                valid_mask = nat_valid & combined_mask
            else:
                valid_mask = combined_mask

            if nat_clamped is not None and nat_clamped.shape == temps_k.shape:
                clamped_mask = nat_clamped
            else:
                clamped_mask = (temps_k <= 180.0) & valid_mask

        return temps_k, valid_mask, clamped_mask

    def get_channel_analytics(
        self,
        storm_or_id: str,
        channel: str,
    ) -> ChannelAnalytics:
        """Compute or retrieve comprehensive physical analytics for a specific channel."""
        record = self.get_crop_provenance(storm_or_id)
        temps_k, valid_mask, clamped_mask = self.load_channel_array(storm_or_id, channel)

        ch_key = channel.upper().replace("_", "-")
        matching = [c for c in record.available_channels if c.upper().replace("_", "-") == ch_key]
        if not matching:
            raise ValueError(
                f"Channel '{channel}' unavailable for {record.storm_name}. "
                f"Available channels: {record.available_channels}"
            )
        norm_ch = matching[0]
        native_res = record.channel_resolutions_km.get(norm_ch, 4.0)
        delivered_res = 4.0 if record.satellite == "INSAT-3DS" else native_res
        resampling = (
            "bilinear" if norm_ch == "WV" and record.satellite == "INSAT-3DR" else "native/none"
        )

        return SatelliteImageAnalyticsEngine.compute_channel_analytics(
            channel_name=norm_ch,
            temps_k=temps_k,
            valid_mask=valid_mask,
            clamped_mask=clamped_mask,
            grid_spacing_km=record.target_grid_spacing_km,
            native_resolution_km=native_res,
            delivered_resolution_km=delivered_res,
            resampling_method=resampling,
            satellite_name=record.satellite,
        )

    def get_channel_preview(
        self,
        storm_or_id: str,
        channel: str,
        colormap: ColormapType = "thermal_ir",
        output_format: Literal["PNG", "WEBP"] = "PNG",
        include_legend: bool = False,
        highlight_clamped: bool = False,
    ) -> bytes:
        """Render and return high-performance cached preview bytes."""
        record = self.get_crop_provenance(storm_or_id)
        ch_key = channel.upper().replace("_", "-")
        matching = [c for c in record.available_channels if c.upper().replace("_", "-") == ch_key]
        if not matching:
            raise ValueError(
                f"Channel '{channel}' unavailable for {record.storm_name}. "
                f"Available channels: {record.available_channels}"
            )
        norm_ch = matching[0]

        # Cache key based on crop checksum, channel, colormap, format, and legend
        cache_slug = f"{record.crop_sha256[:16]}_{norm_ch}_{colormap}_{output_format.lower()}_{int(include_legend)}_{int(highlight_clamped)}"
        ext = "webp" if output_format.upper() == "WEBP" else "png"
        cache_path = self.cache_dir / f"{cache_slug}.{ext}"

        # 1. In-memory cache hit
        if cache_slug in self._memory_cache:
            return self._memory_cache[cache_slug]

        # 2. Disk cache hit
        if cache_path.is_file():
            cached_bytes = cache_path.read_bytes()
            self._memory_cache[cache_slug] = cached_bytes
            return cached_bytes

        # 3. Cache miss: render preview
        temps_k, valid_mask, clamped_mask = self.load_channel_array(storm_or_id, channel)

        if include_legend:
            img = SatelliteVisualizer.render_composite_preview(
                arr_k=temps_k,
                storm_name=record.storm_name,
                channel_name=norm_ch,
                satellite=record.satellite,
                valid_mask=valid_mask,
                clamped_mask=clamped_mask,
                colormap=colormap,
                native_res_km=record.channel_resolutions_km.get(norm_ch, 4.0),
                extent_km=record.crop_extent_km,
            )
            import io

            buf = io.BytesIO()
            if output_format.upper() == "WEBP":
                img.save(buf, format="WEBP", lossless=True)
            else:
                img.save(buf, format="PNG", optimize=True)
            preview_bytes = buf.getvalue()
        else:
            preview_bytes = SatelliteVisualizer.render_to_bytes(
                arr_k=temps_k,
                valid_mask=valid_mask,
                clamped_mask=clamped_mask,
                colormap=colormap,
                output_format=output_format,
                highlight_clamped=highlight_clamped,
            )

        # Write to disk cache and in-memory cache
        try:
            cache_path.write_bytes(preview_bytes)
        except Exception as e:
            logger.warning("Failed to write preview disk cache: %s", e)

        self._memory_cache[cache_slug] = preview_bytes
        return preview_bytes

    def pre_render_all_authentic_previews(self) -> dict[str, Any]:
        """Pre-render all authentic crop previews across channels and colormaps.

        Generates offline demo cache and ensures instant UI switching.
        """
        results: list[dict[str, Any]] = []
        colormaps: list[ColormapType] = ["thermal_ir", "grayscale_inv", "dvorak_bd", "water_vapor"]

        for storm_name, record in AUTHENTIC_SATELLITE_REGISTRY.items():
            storm_summary: dict[str, Any] = {
                "storm": storm_name,
                "crop_sha256": record.crop_sha256,
                "rendered_previews": 0,
                "channels": [],
            }
            for ch in record.available_channels:
                ch_entry: dict[str, Any] = {"channel": ch, "previews": []}
                # Precompute analytics and save JSON companion
                analytics = self.get_channel_analytics(storm_name, ch)
                analytics_json = self.cache_dir / f"{record.crop_sha256[:16]}_{ch}_analytics.json"
                analytics_json.write_text(json.dumps(analytics.to_dict(), indent=2))

                for cm in colormaps:
                    # Select relevant colormaps for channels (water_vapor primarily for WV)
                    if cm == "water_vapor" and ch != "WV":
                        continue
                    if cm == "dvorak_bd" and ch not in ("TIR-1", "TIR-2"):
                        continue

                    # Pre-render standard PNG
                    png_bytes = self.get_channel_preview(
                        storm_or_id=storm_name,
                        channel=ch,
                        colormap=cm,
                        output_format="PNG",
                        include_legend=False,
                    )
                    # Pre-render composite with legend
                    composite_bytes = self.get_channel_preview(
                        storm_or_id=storm_name,
                        channel=ch,
                        colormap=cm,
                        output_format="PNG",
                        include_legend=True,
                    )
                    ch_entry["previews"].append(
                        {
                            "colormap": cm,
                            "bytes_raw": len(png_bytes),
                            "bytes_composite": len(composite_bytes),
                        }
                    )
                    storm_summary["rendered_previews"] += 2

                storm_summary["channels"].append(ch_entry)
            results.append(storm_summary)

        # Write overall offline cache catalog
        catalog_path = self.cache_dir / "authentic_offline_preview_manifest.json"
        catalog_data = {
            "version": "1.0.0",
            "status": "OFFLINE_DEMO_CACHE_READY",
            "storms_cached": [s["storm"] for s in results],
            "details": results,
        }
        catalog_path.write_text(json.dumps(catalog_data, indent=2))
        logger.info(
            "Pre-rendered offline satellite preview cache complete: %d storms", len(results)
        )
        return catalog_data


# Singleton service instance
_satellite_service_instance: SatelliteImageService | None = None


def get_satellite_service() -> SatelliteImageService:
    """Retrieve or initialize singleton SatelliteImageService."""
    global _satellite_service_instance
    if _satellite_service_instance is None:
        _satellite_service_instance = SatelliteImageService()
    return _satellite_service_instance
