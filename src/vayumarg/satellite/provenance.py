"""Scientific Provenance and Ground-Truth Track Association Registry.

Maintains verified historical cyclone track associations, sensor metadata,
agency lineage (IMD 3-min vs JTWC 1-min wind segregations), and task-level
eligibility policies for authentic INSAT satellite observations.
"""

from dataclasses import asdict, dataclass
from typing import Any

DANA_IMD_INELIGIBILITY_NOTICE = (
    "Authentic INSAT-3DS observation — primary IMD classification label unavailable "
    "under this study's eligibility policy."
)


@dataclass(frozen=True)
class GroundTruthObservation:
    """Official cyclone intensity observation from a meteorological agency."""

    agency: str  # "IMD" or "JTWC"
    averaging_period: str  # "3-minute sustained" or "1-minute sustained"
    wind_speed_knots: float | None
    central_pressure_hpa: float | None
    cyclone_category: str | None  # e.g., "SCS", "ESCS", "VSCS", "TY", "TS"
    reference_timestamp_utc: str
    latitude: float
    longitude: float
    is_retrospective_best_track: bool
    is_primary_target: bool


@dataclass(frozen=True)
class ProvenanceRecord:
    """Complete provenance and calibration lineage for an authentic satellite crop."""

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
    verification_status: str  # Strictly "REAL_VERIFIED"
    acquisition_start_utc: str
    estimated_local_scan_time_utc: str
    scan_time_uncertainty: str
    temporal_offset_minutes: float
    spatial_offset_km: float
    crop_extent_km: float
    target_grid_spacing_km: float
    center_latitude: float
    center_longitude: float
    available_channels: list[str]
    channel_resolutions_km: dict[str, float]
    # Current-State Labels & Eligibility
    primary_imd_eligible: bool
    primary_imd_observation: GroundTruthObservation | None
    secondary_jtwc_observation: GroundTruthObservation | None
    dana_ineligibility_notice: str | None
    exclusion_reason: str | None
    model_eligibility: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        """Convert provenance record to JSON-serializable dictionary."""
        return asdict(self)


# Authoritative Verified Registry for the 4 Authentic Satellite Granules & Crops
AUTHENTIC_SATELLITE_REGISTRY: dict[str, ProvenanceRecord] = {
    "REMAL": ProvenanceRecord(
        crop_id="e93002d6-a5e2-4ae2-8adf-fa7a50d0da36",
        storm_name="REMAL",
        canonical_storm_sid="2024145N14087",
        season_year=2024,
        ocean_basin="Bay of Bengal (NI)",
        satellite="INSAT-3DR",
        sensor="IMAGER",
        product_code="3RIMG_L1B_STD",
        source_filename="3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5",
        source_sha256="5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807",
        crop_filename="REMAL_20240526_1802_MULTICHANNEL.h5",
        crop_sha256="7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90",
        verification_status="REAL_VERIFIED",
        acquisition_start_utc="2024-05-26T18:02:00Z",
        estimated_local_scan_time_utc="2024-05-26T18:04:30Z",
        scan_time_uncertainty="+/- 2.0 min (rapid scan sector 18:02:58 to 18:07:16 UTC)",
        temporal_offset_minutes=-2.0,
        spatial_offset_km=1.03,
        crop_extent_km=800.0,
        target_grid_spacing_km=4.0,
        center_latitude=21.70,
        center_longitude=89.20,
        available_channels=["TIR-1", "WV", "TIR-2", "MIR"],
        channel_resolutions_km={"TIR-1": 4.0, "WV": 8.0, "TIR-2": 4.0, "MIR": 4.0},
        primary_imd_eligible=True,
        primary_imd_observation=GroundTruthObservation(
            agency="IMD",
            averaging_period="3-minute sustained",
            wind_speed_knots=60.0,
            central_pressure_hpa=978.0,
            cyclone_category="SCS",
            reference_timestamp_utc="2024-05-26T18:00:00Z",
            latitude=22.0,
            longitude=88.9,
            is_retrospective_best_track=True,
            is_primary_target=True,
        ),
        secondary_jtwc_observation=GroundTruthObservation(
            agency="JTWC",
            averaging_period="1-minute sustained",
            wind_speed_knots=55.0,
            central_pressure_hpa=979.0,
            cyclone_category="TS",
            reference_timestamp_utc="2024-05-26T18:00:00Z",
            latitude=22.0,
            longitude=88.9,
            is_retrospective_best_track=True,
            is_primary_target=False,
        ),
        dana_ineligibility_notice=None,
        exclusion_reason=None,
        model_eligibility={
            "general_atmospheric_research": True,
            "primary_imd_category_classification": True,
            "primary_imd_wind_intensity_regression": True,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": False,
        },
    ),
    "DANA": ProvenanceRecord(
        crop_id="869cd46b-659a-430a-8a45-d2fd8ad7174b",
        storm_name="DANA",
        canonical_storm_sid="2024295N15092",
        season_year=2024,
        ocean_basin="Bay of Bengal (NI)",
        satellite="INSAT-3DS",
        sensor="IMAGER",
        product_code="3SIMG_L1B_STD",
        source_filename="3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5",
        source_sha256="98f3e5640bbc8c1d42da0fd090c0b93ead2d239718946ce69c25d59921ad4fcf",
        crop_filename="DANA_20241025_2330_MULTICHANNEL.h5",
        crop_sha256="71915613322d06949b43b6a6343359fad58c5e8c82603216ef4229efc12b9463",
        verification_status="REAL_VERIFIED",
        acquisition_start_utc="2024-10-25T23:30:00Z",
        estimated_local_scan_time_utc="2024-10-25T23:32:15Z",
        scan_time_uncertainty="+/- 2.0 min (rapid scan sector 23:30:12 to 23:34:29 UTC)",
        temporal_offset_minutes=30.0,
        spatial_offset_km=0.00,
        crop_extent_km=800.0,
        target_grid_spacing_km=4.0,
        center_latitude=21.20,
        center_longitude=86.40,
        available_channels=["TIR-1", "WV", "TIR-2", "MIR"],
        channel_resolutions_km={"TIR-1": 4.0, "WV": 8.0, "TIR-2": 4.0, "MIR": 4.0},
        primary_imd_eligible=False,
        primary_imd_observation=None,
        secondary_jtwc_observation=GroundTruthObservation(
            agency="JTWC",
            averaging_period="1-minute sustained",
            wind_speed_knots=20.0,
            central_pressure_hpa=1000.0,
            cyclone_category="DB",
            reference_timestamp_utc="2024-10-26T00:00:00Z",
            latitude=21.2,
            longitude=86.4,
            is_retrospective_best_track=True,
            is_primary_target=False,
        ),
        dana_ineligibility_notice=DANA_IMD_INELIGIBILITY_NOTICE,
        exclusion_reason=(
            "Primary IMD best-track cyclonic classification terminated at 18:00 UTC (Depression, 25 kt). "
            "By 00:00 UTC 26 Oct 2024, IMD documented DANA weakened into a Well Marked Low Pressure Area (WML < 17 kt), "
            "ending official cyclone categorization."
        ),
        model_eligibility={
            "general_atmospheric_research": True,
            "primary_imd_category_classification": False,
            "primary_imd_wind_intensity_regression": False,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": True,
        },
    ),
    "AMPHAN": ProvenanceRecord(
        crop_id="142da9e9-417e-428b-acba-b68e3aab0199",
        storm_name="AMPHAN",
        canonical_storm_sid="2020136N10088",
        season_year=2020,
        ocean_basin="Bay of Bengal (NI)",
        satellite="INSAT-3DR",
        sensor="IMAGER",
        product_code="3RIMG_L1B_STD",
        source_filename="3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5",
        source_sha256="032cde43fbd6741fd85e86e118144f63137c60f7ce023555cdf04ac38a3f0abb",
        crop_filename="AMPHAN_20200519_2358_MULTICHANNEL.h5",
        crop_sha256="86a14fcb9109c32cf6955bc7739202b9a86d08928a6df1ee503e3ba9a3e28b12",
        verification_status="REAL_VERIFIED",
        acquisition_start_utc="2020-05-19T23:58:00Z",
        estimated_local_scan_time_utc="2020-05-20T00:00:15Z",
        scan_time_uncertainty="+/- 2.0 min (rapid scan sector 23:58:07 to 00:02:24 UTC)",
        temporal_offset_minutes=2.0,
        spatial_offset_km=0.00,
        crop_extent_km=800.0,
        target_grid_spacing_km=4.0,
        center_latitude=19.10,
        center_longitude=87.50,
        available_channels=["TIR-1", "WV", "TIR-2", "MIR"],
        channel_resolutions_km={"TIR-1": 4.0, "WV": 8.0, "TIR-2": 4.0, "MIR": 4.0},
        primary_imd_eligible=True,
        primary_imd_observation=GroundTruthObservation(
            agency="IMD",
            averaging_period="3-minute sustained",
            wind_speed_knots=95.0,
            central_pressure_hpa=952.0,
            cyclone_category="ESCS",
            reference_timestamp_utc="2020-05-20T00:00:00Z",
            latitude=19.2,
            longitude=87.5,
            is_retrospective_best_track=True,
            is_primary_target=True,
        ),
        secondary_jtwc_observation=GroundTruthObservation(
            agency="JTWC",
            averaging_period="1-minute sustained",
            wind_speed_knots=100.0,
            central_pressure_hpa=947.0,
            cyclone_category="TY",
            reference_timestamp_utc="2020-05-20T00:00:00Z",
            latitude=19.2,
            longitude=87.5,
            is_retrospective_best_track=True,
            is_primary_target=False,
        ),
        dana_ineligibility_notice=None,
        exclusion_reason=None,
        model_eligibility={
            "general_atmospheric_research": True,
            "primary_imd_category_classification": True,
            "primary_imd_wind_intensity_regression": True,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": False,
        },
    ),
    "BIPARJOY": ProvenanceRecord(
        crop_id="fc074478-42dd-4d02-b86f-8eb109cc9872",
        storm_name="BIPARJOY",
        canonical_storm_sid="2023156N10067",
        season_year=2023,
        ocean_basin="Arabian Sea (NI)",
        satellite="INSAT-3DR",
        sensor="IMAGER",
        product_code="3RIMG_L1B_STD",
        source_filename="3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5",
        source_sha256="b2f15cae5139468e2bac1804fd25138bff402b266c7939a7f2cd91a4b5a15220",
        crop_filename="BIPARJOY_20230612_2358_MULTICHANNEL.h5",
        crop_sha256="a4ce1ee39cb21cc016fb7d2cd929d775f31773ef4813d8cfc351f60cac1a835c",
        verification_status="REAL_VERIFIED",
        acquisition_start_utc="2023-06-12T23:58:00Z",
        estimated_local_scan_time_utc="2023-06-13T00:00:35Z",
        scan_time_uncertainty="+/- 2.0 min (rapid scan sector 23:58:30 to 00:02:47 UTC)",
        temporal_offset_minutes=2.0,
        spatial_offset_km=0.00,
        crop_extent_km=800.0,
        target_grid_spacing_km=4.0,
        center_latitude=20.60,
        center_longitude=67.00,
        available_channels=["TIR-1", "WV", "TIR-2", "MIR"],
        channel_resolutions_km={"TIR-1": 4.0, "WV": 8.0, "TIR-2": 4.0, "MIR": 4.0},
        primary_imd_eligible=True,
        primary_imd_observation=GroundTruthObservation(
            agency="IMD",
            averaging_period="3-minute sustained",
            wind_speed_knots=85.0,
            central_pressure_hpa=962.0,
            cyclone_category="VSCS",
            reference_timestamp_utc="2023-06-13T00:00:00Z",
            latitude=20.7,
            longitude=67.0,
            is_retrospective_best_track=True,
            is_primary_target=True,
        ),
        secondary_jtwc_observation=GroundTruthObservation(
            agency="JTWC",
            averaging_period="1-minute sustained",
            wind_speed_knots=85.0,
            central_pressure_hpa=961.0,
            cyclone_category="TY",
            reference_timestamp_utc="2023-06-13T00:00:00Z",
            latitude=20.7,
            longitude=67.0,
            is_retrospective_best_track=True,
            is_primary_target=False,
        ),
        dana_ineligibility_notice=None,
        exclusion_reason=None,
        model_eligibility={
            "general_atmospheric_research": True,
            "primary_imd_category_classification": True,
            "primary_imd_wind_intensity_regression": True,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": False,
        },
    ),
}


def get_provenance_by_identifier(identifier: str) -> ProvenanceRecord | None:
    """Retrieve verified provenance record by storm name or crop ID."""
    clean_id = identifier.strip().upper()
    if clean_id in AUTHENTIC_SATELLITE_REGISTRY:
        return AUTHENTIC_SATELLITE_REGISTRY[clean_id]

    for record in AUTHENTIC_SATELLITE_REGISTRY.values():
        if record.crop_id.lower() == identifier.lower() or record.crop_filename.upper() == clean_id:
            return record

    return None
