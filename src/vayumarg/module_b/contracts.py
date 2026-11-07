"""Module B Contracts: Independent Cyclone Track & Future Wind Prediction.

Defines input/output contracts for multi-step track and intensity forecasting
and hindsight verification adhering to WMO/IMD scientific conventions.

ARCHITECTURAL PRINCIPLE:
Module B operates strictly and independently on foundational historical tracks.
Forecast inputs contain NO observations later than issue timestamp T.
Future records are permitted ONLY in a separate hindsight-verification path.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RecordType(StrEnum):
    HISTORICAL_INPUT = "HISTORICAL_INPUT"
    BASELINE_FORECAST = "BASELINE_FORECAST"
    FUTURE_OBSERVATION_FOR_VERIFICATION = "FUTURE_OBSERVATION_FOR_VERIFICATION"


class ForecastStatus(StrEnum):
    SUCCESS = "SUCCESS"
    UNAVAILABLE = "UNAVAILABLE"


class BaseModuleBModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class HistoricalObservationPoint(BaseModuleBModel):
    """Historical observation fix consumed strictly up to issue time."""

    observation_time_utc: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    wind_speed_knots: float | None = Field(default=None, ge=0.0, le=300.0)
    central_pressure_hpa: float | None = Field(default=None, ge=800.0, le=1080.0)
    averaging_period: str = "3-min"
    imd_category: str | None = None
    source_record_id: str | None = None
    record_type: RecordType = RecordType.HISTORICAL_INPUT


class MotionVector(BaseModuleBModel):
    """Estimated forward translation velocity vector derived from usable historical fixes."""

    speed_kmh: float = Field(..., ge=0.0)
    bearing_deg: float = Field(..., ge=0.0, le=360.0)
    displacement_km: float = Field(..., ge=0.0)
    delta_hours: float = Field(..., gt=0.0)
    source_fix_prev_utc: datetime
    source_fix_curr_utc: datetime


class ForecastHorizonPoint(BaseModuleBModel):
    """Single predicted future track coordinate and intensity step."""

    lead_time_hours: int = Field(..., ge=1, le=168)
    valid_time_utc: datetime
    predicted_latitude: float = Field(..., ge=-90.0, le=90.0)
    predicted_longitude: float = Field(..., ge=-180.0, le=180.0)
    projected_distance_km: float = Field(..., ge=0.0)
    predicted_wind_persistence_knots: float | None = Field(default=None, ge=0.0, le=250.0)
    predicted_wind_trend_knots: float | None = Field(default=None, ge=0.0, le=250.0)
    predicted_imd_category_persistence: str | None = None
    predicted_imd_category_trend: str | None = None
    uncertainty_radius_km: float = Field(..., ge=0.0)
    record_type: RecordType = RecordType.BASELINE_FORECAST


class GeoJsonFeature(BaseModuleBModel):
    """Standard RFC 7946 GeoJSON Feature with [longitude, latitude] coordinates."""

    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class GeoJsonFeatureCollection(BaseModuleBModel):
    """Standard RFC 7946 GeoJSON FeatureCollection."""

    type: str = "FeatureCollection"
    features: list[GeoJsonFeature]


class CycloneForecastOutput(BaseModuleBModel):
    """Complete canonical forecast output strictly isolated from future observations."""

    forecast_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    status: ForecastStatus = ForecastStatus.SUCCESS
    unavailability_reason: str | None = None
    storm_id: str
    storm_sid: str
    storm_name: str
    season_year: int
    primary_basin: str
    source_agency: str
    wind_averaging_period: str
    issue_time_utc: datetime
    input_observation_count: int
    current_position: HistoricalObservationPoint | None = None
    translational_motion: MotionVector | None = None
    forecast_horizons: list[ForecastHorizonPoint] = Field(default_factory=list)
    historical_track_used: list[HistoricalObservationPoint] = Field(default_factory=list)
    geojson: GeoJsonFeatureCollection | None = None
    methodology: str = (
        "Great-Circle Geodesic Constant-Velocity Extrapolation + "
        "Persistence & Bounded-Trend Wind Intensity Baseline"
    )
    limitations: str = (
        "Deterministic kinematic reference model. Does not simulate baroclinic environmental "
        "steering, vertical wind shear, or sea-surface heat flux."
    )
    provenance_note: str = (
        "Strict temporal boundary enforced: no observation with timestamp > issue_time_utc "
        "is queried or utilized in prediction. Retrospective best tracks serve as simulated real-time inputs."
    )
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HindsightHorizonVerification(BaseModuleBModel):
    """Verification comparison for a single forecast horizon against retrospective ground truth."""

    lead_time_hours: int
    valid_time_utc: datetime
    target_status: str  # "VERIFIED" or "TARGET_UNAVAILABLE"
    predicted_latitude: float
    predicted_longitude: float
    actual_observation_time_utc: datetime | None = None
    actual_latitude: float | None = None
    actual_longitude: float | None = None
    geodesic_track_error_km: float | None = None
    predicted_wind_persistence_kt: float | None = None
    predicted_wind_trend_kt: float | None = None
    actual_wind_kt: float | None = None
    persistence_wind_error_kt: float | None = None
    trend_wind_error_kt: float | None = None
    actual_category: str | None = None
    record_type: RecordType = RecordType.FUTURE_OBSERVATION_FOR_VERIFICATION
    notes: str | None = None


class HindsightVerificationOutput(BaseModuleBModel):
    """Separate hindsight verification report computed only post-prediction."""

    storm_id: str
    storm_sid: str
    storm_name: str
    source_agency: str
    issue_time_utc: datetime
    verification_tolerance_hours: float
    horizons_evaluated: int
    horizons_matched: int
    mean_track_error_km: float | None = None
    mean_wind_error_persistence_kt: float | None = None
    mean_wind_error_trend_kt: float | None = None
    verification_horizons: list[HindsightHorizonVerification]
    geojson: GeoJsonFeatureCollection | None = None
    provenance_note: str = (
        "Evaluated strictly post-prediction in a separate verification path. "
        "Actual observations are retrospective best-track fixes."
    )
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
