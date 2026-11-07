"""Module A Contracts: Satellite Current-State Classification & Intensity.

Team: Ishhan, Ishika, Kirti.

Defines typed interfaces for satellite imagery inputs, current-state Dvorak
features, physical satellite analytics, and current cyclone intensity classification outputs.
"""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from vayumarg.contracts.enums import IMDCategory


class SatelliteFeatureContract(BaseModel):
    """Satellite observation input contract for Module A."""

    source_asset_id: uuid.UUID
    satellite_name: str = Field(..., max_length=50)  # e.g., INSAT-3D, INSAT-3DR, Kalpana-1
    sensor_name: str = Field(..., max_length=50)  # e.g., IMAGER
    channel_name: str = Field(..., max_length=20)  # e.g., TIR1 (10.8 um), MIR (3.9 um), VIS
    acquisition_time_utc: datetime
    center_latitude: float = Field(..., ge=-90.0, le=90.0)
    center_longitude: float = Field(..., ge=-180.0, le=180.0)
    spatial_resolution_km: float = Field(..., gt=0)
    grid_shape: tuple[int, int] = (128, 128)
    array_storage_uri: str = Field(..., max_length=1024)
    array_sha256: str = Field(..., min_length=64, max_length=64)


class ModuleAIntensityEstimationOutput(BaseModel):
    """Output contract produced by Module A models."""

    estimation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    storm_id: uuid.UUID
    satellite_feature_id: uuid.UUID
    reference_timestamp_utc: datetime
    estimated_wind_speed_knots: float = Field(..., ge=0.0, le=250.0)
    estimated_imd_category: IMDCategory
    confidence_interval_knots: tuple[float, float]
    dvorak_t_number: float | None = Field(default=None, ge=1.0, le=8.5)
    model_version: str = Field(..., max_length=50)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SatelliteCropSummaryContract(BaseModel):
    """Summary of an authentic verified multichannel satellite crop."""

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
    verification_status: str = "REAL_VERIFIED"
    acquisition_start_utc: str
    estimated_local_scan_time_utc: str
    scan_time_uncertainty: str
    extent_km: float = 800.0
    target_grid_spacing_km: float = 4.0
    center_latitude: float
    center_longitude: float
    available_channels: list[str]
    primary_imd_eligible: bool
    dana_ineligibility_notice: str | None = None


class CurrentStateLabelsContract(BaseModel):
    """Official historical track association and ground-truth intensity labels."""

    storm_name: str
    canonical_storm_sid: str
    acquisition_time_utc: str
    primary_imd_eligible: bool
    dana_ineligibility_notice: str | None = None
    primary_imd_wind_knots: float | None = None
    primary_imd_central_pressure_hpa: float | None = None
    primary_imd_category: str | None = None
    secondary_jtwc_wind_knots: float | None = None
    secondary_jtwc_pressure_hpa: float | None = None
    secondary_jtwc_category: str | None = None
    temporal_offset_minutes: float
    spatial_offset_km: float
    model_eligibility: dict[str, bool] = Field(default_factory=dict)
