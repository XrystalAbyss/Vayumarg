"""Schemas for satellite crops and physical brightness temperature metrics."""

from typing import Any

from pydantic import BaseModel, Field


class SatelliteCropMeta(BaseModel):
    """Metadata describing an authentic multi-channel INSAT crop."""

    storm_name: str
    year: int
    sensor: str
    crop_filename: str
    file_size_bytes: int
    supported_channels: list[str] = Field(default_factory=lambda: ["TIR-1", "TIR-2", "WV", "MIR"])
    grid_resolution_km: float = 4.0
    physical_extent_km: float = 800.0
    grid_shape: list[int] = Field(default_factory=lambda: [200, 200])
    provenance: str = "ISRO MOSDAC Level 1B Standard Standardised Grid"
    science_disclaimer: str = (
        "Authentic satellite imagery. Descriptive physical features only."
    )


class PhysicalCropMetrics(BaseModel):
    """Calculated brightness-temperature features and cloud-top distributions."""

    storm_name: str
    satellite_sensor: str
    crop_filename: str
    channel: str
    grid_shape: list[int]
    spatial_resolution_km: float
    physical_extent_km: list[float]
    valid_pixels: int
    total_pixels: int
    valid_pixel_ratio: float
    temperature_quantiles_kelvin: dict[str, float]
    cold_cloud_analytics: dict[str, Any]
    radial_temperature_profile: dict[str, Any]
    azimuthal_symmetry_index: float
    clamped_low_temperature_pixels: int
    clamped_warning: bool
    crop_metadata: dict[str, Any]
    science_disclaimer: str | None = None

