"""Satellite image processing, crop retrieval, and brightness temperature analytics service."""

from typing import Any

from vayumarg.satellite.preview import (
    compute_physical_crop_metrics,
    render_crop_png,
)
from vayumarg.services.cyclone_service import CROPS_DIR, STORM_REGISTRY, TARGET_STORMS


class SatelliteService:
    """Encapsulates satellite crop retrieval, image rendering, and radiometric calculations."""

    @staticmethod
    def list_crops() -> list[dict[str, Any]]:
        """List all authentic multi-channel INSAT crops available on disk."""
        items = []
        for item in TARGET_STORMS:
            if not item["crop"]:
                continue
            crop_path = CROPS_DIR / item["crop"]
            if not crop_path.is_file():
                continue

            items.append(
                {
                    "storm_name": item["name"],
                    "year": item["year"],
                    "sensor": item["sensor"],
                    "crop_filename": item["crop"],
                    "file_size_bytes": crop_path.stat().st_size,
                    "supported_channels": ["TIR-1", "TIR-2", "WV", "MIR"],
                    "grid_resolution_km": 4.0,
                    "physical_extent_km": 800.0,
                    "grid_shape": [200, 200],
                    "provenance": "ISRO MOSDAC Level 1B Standard Standardised Grid",
                    "science_disclaimer": "Authentic satellite imagery. Descriptive physical features only.",
                }
            )
        return items

    @staticmethod
    def render_crop_image(storm_name: str, channel: str = "TIR-1") -> bytes:
        """Render authentic HDF5 crop channel as PNG image bytes."""
        name_upper = storm_name.upper()
        reg = STORM_REGISTRY.get(name_upper)
        if not reg or not reg.get("crop_filename"):
            raise KeyError(f"No satellite crop registered for '{storm_name}'")

        crop_path = CROPS_DIR / reg["crop_filename"]
        if not crop_path.is_file():
            raise FileNotFoundError(f"HDF5 file missing on disk: {crop_path.name}")

        return render_crop_png(crop_path, channel=channel.upper())

    @staticmethod
    def compute_metrics(storm_name: str, channel: str = "TIR-1") -> dict[str, Any]:
        """Compute physical brightness-temperature features and cold-cloud fractions from authentic HDF5 crop."""
        name_upper = storm_name.upper()
        reg = STORM_REGISTRY.get(name_upper)
        if not reg or not reg.get("crop_filename"):
            raise KeyError(f"No satellite crop registered for '{storm_name}'")

        crop_path = CROPS_DIR / reg["crop_filename"]
        if not crop_path.is_file():
            raise FileNotFoundError(f"HDF5 file missing on disk: {crop_path.name}")

        metrics = compute_physical_crop_metrics(crop_path, channel=channel.upper())
        metrics["storm_name"] = name_upper
        metrics["satellite_sensor"] = reg.get("satellite_sensor", "INSAT-3DR")
        metrics["crop_filename"] = reg.get("crop_filename")
        return metrics

