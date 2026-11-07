"""Scientific and operational enumerations for Vayumarg.

Standardizes cyclone basins, meteorological agency conventions,
wind averaging periods, IMD cyclone intensity classifications,
and data quality flags.
"""

from enum import StrEnum


class Basin(StrEnum):
    """Ocean basin codes based on WMO and IBTrACS standards."""

    BOB = "BOB"  # Bay of Bengal (North Indian Ocean)
    ARB = "ARB"  # Arabian Sea (North Indian Ocean)
    NIO = "NIO"  # North Indian Ocean (composite/undifferentiated)
    WP = "WP"  # Western North Pacific
    EP = "EP"  # Eastern North Pacific
    CP = "CP"  # Central North Pacific
    NA = "NA"  # North Atlantic
    SI = "SI"  # South Indian Ocean
    SP = "SP"  # South Pacific
    SA = "SA"  # South Atlantic


class Agency(StrEnum):
    """Meteorological agency and data provider codes."""

    IMD = "IMD"  # India Meteorological Department (RSMC New Delhi)
    JTWC = "JTWC"  # Joint Typhoon Warning Center
    IBTRACS = "IBTRACS"  # International Best Track Archive for Climate Stewardship
    JMA = "JMA"  # Japan Meteorological Agency (RSMC Tokyo)
    CMA = "CMA"  # China Meteorological Administration
    BOM = "BOM"  # Australian Bureau of Meteorology
    NHC = "NHC"  # National Hurricane Center (RSMC Miami)
    CPHC = "CPHC"  # Central Pacific Hurricane Center (Honolulu)
    MOSDAC = "MOSDAC"  # Meteorological and Oceanographic Satellite Data Archival Centre (ISRO)


class AveragingPeriod(StrEnum):
    """Wind speed sustained averaging period conventions.

    CRITICAL SCIENTIFIC DISTINCTION:
    - IMD (RSMC New Delhi) standard: 3-minute sustained wind.
    - JTWC / NHC standard: 1-minute sustained wind.
    - WMO / JMA / BOM standard: 10-minute sustained wind.
    These values cannot be conflated without validated scientific transformations.
    """

    ONE_MINUTE = "1-min"
    THREE_MINUTE = "3-min"
    TEN_MINUTE = "10-min"
    UNKNOWN = "unknown"


class WindUnit(StrEnum):
    """Wind speed measurement units."""

    KNOTS = "kt"
    MPS = "m/s"
    KMPH = "km/h"


class IMDCategory(StrEnum):
    """Official India Meteorological Department (IMD) Cyclone Intensity Scale.

    Based on 3-minute sustained maximum surface winds (MSW).
    Reference: IMD Cyclone Manual & SOP for Cyclone Warning (RSMC New Delhi).
    """

    LOW_PRESSURE_AREA = "LOW"  # < 17 knots (< 31 km/h)
    DEPRESSION = "D"  # 17 - 27 knots (31 - 49 km/h)
    DEEP_DEPRESSION = "DD"  # 28 - 33 knots (50 - 61 km/h)
    CYCLONIC_STORM = "CS"  # 34 - 47 knots (62 - 88 km/h)
    SEVERE_CYCLONIC_STORM = "SCS"  # 48 - 63 knots (89 - 117 km/h)
    VERY_SEVERE_CYCLONIC_STORM = "VSCS"  # 64 - 89 knots (118 - 166 km/h)
    EXTREMELY_SEVERE_CYCLONIC_STORM = "ESCS"  # 90 - 119 knots (167 - 221 km/h)
    SUPER_CYCLONIC_STORM = "SuCS"  # >= 120 knots (>= 222 km/h)


class IssueSeverity(StrEnum):
    """Data quality and integrity issue severity levels."""

    CRITICAL = "CRITICAL"  # Record rejected or invalid for modeling
    WARNING = "WARNING"  # Record accepted but flagged for investigation
    INFO = "INFO"  # Informational note (e.g., interpolated observation)


class ResolutionStatus(StrEnum):
    """Data quality issue resolution lifecycle status."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"
    ACCEPTED_EXCEPTION = "ACCEPTED_EXCEPTION"


class AssetType(StrEnum):
    """Type of ingested scientific asset."""

    TRACK_CSV = "TRACK_CSV"
    BEST_TRACK_NETCDF = "BEST_TRACK_NETCDF"
    SATELLITE_HDF5 = "SATELLITE_HDF5"
    SATELLITE_NETCDF = "SATELLITE_NETCDF"
    METEOROLOGICAL_BULLETIN = "METEOROLOGICAL_BULLETIN"
    PROCESSED_FEATURE_ARRAY = "PROCESSED_FEATURE_ARRAY"


class RunStatus(StrEnum):
    """Status of an automated ingestion run."""

    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class ProvenanceStatus(StrEnum):
    """Raw asset source provenance classification."""

    AUTHENTIC_SOURCE_VERIFIED = "AUTHENTIC_SOURCE_VERIFIED"
    REAL_VERIFIED = "REAL_VERIFIED"  # Backwards-compatible alias for authentic granules
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    PROVENANCE_UNVERIFIED = "PROVENANCE_UNVERIFIED"


class ScientificQualityStatus(StrEnum):
    """Scientific validation states for remote-sensing data processing."""

    RADIOMETRY_VALIDATED = "RADIOMETRY_VALIDATED"
    GEOLOCATION_VALIDATED = "GEOLOCATION_VALIDATED"
    TEMPORAL_ALIGNMENT_VALIDATED = "TEMPORAL_ALIGNMENT_VALIDATED"
    LABEL_VALIDATED = "LABEL_VALIDATED"
    CALIBRATION_CLAMPED = "CALIBRATION_CLAMPED"  # Pixels at lower LUT boundary
    GEOLOCATION_RESIDUAL = "GEOLOCATION_RESIDUAL"  # Sub-pixel quantization residual
    INTER_AGENCY_DISCORDANCE = "INTER_AGENCY_DISCORDANCE"  # Best-track center difference
    DAYLIGHT_ABSENT = "DAYLIGHT_ABSENT"  # Nocturnal acquisition for VIS/SWIR


class ModelEligibility(StrEnum):
    """Machine learning training and benchmarking eligibility governance."""

    MODEL_ELIGIBLE = "MODEL_ELIGIBLE"  # Passes radiometry, geolocation, alignment, and label
    RESEARCH_HOLD = "RESEARCH_HOLD"  # Valid asset held for quality/agency investigation
    INELIGIBLE = "INELIGIBLE"  # Space-fill, excessive missingness, or uncalibrated
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"  # Quarantined mock fixture
