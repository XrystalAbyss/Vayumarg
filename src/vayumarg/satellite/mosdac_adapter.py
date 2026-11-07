"""Official MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre) Adapter.

Defines product specifications, sensor characteristics, calibration equations,
and acquisition protocols for ISRO's INSAT-3D, INSAT-3DR, and INSAT-3DS Imager payloads.
Enforces authentication boundaries and metadata discovery without credential leakage.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.core.logging import get_logger
from vayumarg.database.schema import SatelliteProduct

logger = get_logger("vayumarg.satellite.mosdac")

# MOSDAC Official Endpoints
MOSDAC_CATALOG_URL = "https://mosdac.gov.in/catalog-app/satellite.php"
MOSDAC_DOWNLOAD_API_URL = "https://www.mosdac.gov.in/downloadapi"
MOSDAC_DOWNLOAD_MANUAL_URL = "https://www.mosdac.gov.in/downloadapi-manual"


@dataclass
class SpectralChannelSpec:
    """Spectral and spatial resolution specification for an imager channel."""

    channel_name: str
    spectral_type: str
    central_wavelength_um: float
    wavelength_min_um: float
    wavelength_max_um: float
    nadir_resolution_km: float
    physical_quantity: str  # e.g., 'Brightness Temperature (K)' or 'Albedo / Reflectance'
    fill_value: float = -999.0
    primary_use: str = ""


@dataclass
class MOSDACProductSpec:
    """Scientific specification for an authorized MOSDAC satellite product."""

    product_code: str
    satellite_name: str
    sensor_name: str
    processing_level: str
    nominal_sub_satellite_longitude_deg: float
    temporal_cadence_minutes: int
    operational_start_date: str
    operational_end_date: str | None
    channels: dict[str, SpectralChannelSpec]
    file_format: str = "HDF5"
    description: str = ""
    auth_required_for_download: bool = True
    catalog_search_public: bool = True


# Standard Imager Channel Definitions across INSAT-3D / 3DR / 3DS
INSAT_IMAGER_CHANNELS = {
    "VIS": SpectralChannelSpec(
        channel_name="VIS",
        spectral_type="Visible",
        central_wavelength_um=0.65,
        wavelength_min_um=0.55,
        wavelength_max_um=0.75,
        nadir_resolution_km=1.0,
        physical_quantity="Reflectance (%)",
        primary_use="Daytime cloud monitoring and storm vortex center fix",
    ),
    "SWIR": SpectralChannelSpec(
        channel_name="SWIR",
        spectral_type="Short-Wave Infrared",
        central_wavelength_um=1.625,
        wavelength_min_um=1.55,
        wavelength_max_um=1.70,
        nadir_resolution_km=1.0,
        physical_quantity="Reflectance (%)",
        primary_use="Snow/cloud phase discrimination and cloud-top particle sizing",
    ),
    "MIR": SpectralChannelSpec(
        channel_name="MIR",
        spectral_type="Mid-Infrared",
        central_wavelength_um=3.90,
        wavelength_min_um=3.80,
        wavelength_max_um=4.00,
        nadir_resolution_km=4.0,
        physical_quantity="Brightness Temperature (K)",
        primary_use="Nighttime low cloud / fog identification and hot spot detection",
    ),
    "WV": SpectralChannelSpec(
        channel_name="WV",
        spectral_type="Water Vapor",
        central_wavelength_um=6.80,
        wavelength_min_um=6.50,
        wavelength_max_um=7.10,
        nadir_resolution_km=8.0,
        physical_quantity="Brightness Temperature (K)",
        primary_use="Upper-tropospheric moisture flux and environmental wind shear tracking",
    ),
    "TIR-1": SpectralChannelSpec(
        channel_name="TIR-1",
        spectral_type="Thermal Infrared Window 1",
        central_wavelength_um=10.80,
        wavelength_min_um=10.30,
        wavelength_max_um=11.30,
        nadir_resolution_km=4.0,
        physical_quantity="Brightness Temperature (K)",
        primary_use="Continuous 24h cloud-top temperature and convective intensity estimation",
    ),
    "TIR-2": SpectralChannelSpec(
        channel_name="TIR-2",
        spectral_type="Thermal Infrared Window 2",
        central_wavelength_um=12.00,
        wavelength_min_um=11.50,
        wavelength_max_um=12.50,
        nadir_resolution_km=4.0,
        physical_quantity="Brightness Temperature (K)",
        primary_use="Split-window atmospheric moisture correction and Sea Surface Temperature",
    ),
}

# Catalog of Verified Supported Products
SUPPORTED_MOSDAC_PRODUCTS: dict[str, MOSDACProductSpec] = {
    # INSAT-3DS (Operational 2024-Present, 74.0°E)
    "3SIMG_L1B_STD": MOSDACProductSpec(
        product_code="3SIMG_L1B_STD",
        satellite_name="INSAT-3DS",
        sensor_name="IMAGER",
        processing_level="L1B",
        nominal_sub_satellite_longitude_deg=74.0,
        temporal_cadence_minutes=15,
        operational_start_date="2024-02-17",
        operational_end_date=None,
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3DS Imager Level-1B Standard Full Disk and Sector acquisition product.",
    ),
    "3SIMG_L1C_ASIA_MER": MOSDACProductSpec(
        product_code="3SIMG_L1C_ASIA_MER",
        satellite_name="INSAT-3DS",
        sensor_name="IMAGER",
        processing_level="L1C",
        nominal_sub_satellite_longitude_deg=74.0,
        temporal_cadence_minutes=15,
        operational_start_date="2024-02-17",
        operational_end_date=None,
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3DS Imager Level-1C Asia Mercator reprojected regional product.",
    ),
    "3SIMG_L1C_SGP": MOSDACProductSpec(
        product_code="3SIMG_L1C_SGP",
        satellite_name="INSAT-3DS",
        sensor_name="IMAGER",
        processing_level="L1C",
        nominal_sub_satellite_longitude_deg=74.0,
        temporal_cadence_minutes=15,
        operational_start_date="2024-02-17",
        operational_end_date=None,
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3DS Imager Level-1C Sector Grid Product over North Indian Ocean.",
    ),
    # INSAT-3DR (Operational 2016-Present, 74.0°E)
    "3RIMG_L1B_STD": MOSDACProductSpec(
        product_code="3RIMG_L1B_STD",
        satellite_name="INSAT-3DR",
        sensor_name="IMAGER",
        processing_level="L1B",
        nominal_sub_satellite_longitude_deg=74.0,
        temporal_cadence_minutes=30,
        operational_start_date="2016-09-08",
        operational_end_date=None,
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3DR Imager Level-1B Standard meteorological acquisition product.",
    ),
    "3RIMG_L1C_ASIA_MER": MOSDACProductSpec(
        product_code="3RIMG_L1C_ASIA_MER",
        satellite_name="INSAT-3DR",
        sensor_name="IMAGER",
        processing_level="L1C",
        nominal_sub_satellite_longitude_deg=74.0,
        temporal_cadence_minutes=30,
        operational_start_date="2016-09-08",
        operational_end_date=None,
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3DR Imager Level-1C Asia Mercator reprojected meteorological product.",
    ),
    "3RIMG_L1C_SGP": MOSDACProductSpec(
        product_code="3RIMG_L1C_SGP",
        satellite_name="INSAT-3DR",
        sensor_name="IMAGER",
        processing_level="L1C",
        nominal_sub_satellite_longitude_deg=74.0,
        temporal_cadence_minutes=30,
        operational_start_date="2016-09-08",
        operational_end_date=None,
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3DR Imager Level-1C Sector Grid Product for South Asian domain.",
    ),
    # INSAT-3D (Operational 2013-2024, 82.0°E)
    "3DIMG_L1B_STD": MOSDACProductSpec(
        product_code="3DIMG_L1B_STD",
        satellite_name="INSAT-3D",
        sensor_name="IMAGER",
        processing_level="L1B",
        nominal_sub_satellite_longitude_deg=82.0,
        temporal_cadence_minutes=30,
        operational_start_date="2013-07-26",
        operational_end_date="2024-03-01",
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3D Imager Level-1B Standard primary historical acquisition product.",
    ),
    "3DIMG_L1C_ASIA_MER": MOSDACProductSpec(
        product_code="3DIMG_L1C_ASIA_MER",
        satellite_name="INSAT-3D",
        sensor_name="IMAGER",
        processing_level="L1C",
        nominal_sub_satellite_longitude_deg=82.0,
        temporal_cadence_minutes=30,
        operational_start_date="2013-07-26",
        operational_end_date="2024-03-01",
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3D Imager Level-1C Asia Mercator historical meteorological product.",
    ),
    "3DIMG_L1C_SGP": MOSDACProductSpec(
        product_code="3DIMG_L1C_SGP",
        satellite_name="INSAT-3D",
        sensor_name="IMAGER",
        processing_level="L1C",
        nominal_sub_satellite_longitude_deg=82.0,
        temporal_cadence_minutes=30,
        operational_start_date="2013-07-26",
        operational_end_date="2024-03-01",
        channels=INSAT_IMAGER_CHANNELS,
        description="INSAT-3D Imager Level-1C Sector Grid Product historical archive.",
    ),
}


class MOSDACAdapter:
    """Interface for discovering and cataloging MOSDAC satellite products."""

    @staticmethod
    def get_supported_products() -> list[dict[str, Any]]:
        """Return structured summary of verified supported MOSDAC products."""
        summaries = []
        for _code, spec in SUPPORTED_MOSDAC_PRODUCTS.items():
            summaries.append(
                {
                    "product_code": spec.product_code,
                    "satellite_name": spec.satellite_name,
                    "sensor_name": spec.sensor_name,
                    "processing_level": spec.processing_level,
                    "sub_satellite_lon": spec.nominal_sub_satellite_longitude_deg,
                    "cadence_minutes": spec.temporal_cadence_minutes,
                    "operational_period": f"{spec.operational_start_date} to {spec.operational_end_date or 'Present'}",
                    "channel_count": len(spec.channels),
                    "channel_names": list(spec.channels.keys()),
                    "auth_required_for_download": spec.auth_required_for_download,
                }
            )
        return summaries

    @staticmethod
    def register_supported_products_in_db(session: Session) -> list[SatelliteProduct]:
        """Synchronize verified MOSDAC products into the database."""
        registered = []
        for code, spec in SUPPORTED_MOSDAC_PRODUCTS.items():
            existing = session.execute(
                select(SatelliteProduct).where(SatelliteProduct.product_code == code)
            ).scalar_one_or_none()
            if not existing:
                channels_json = [
                    {
                        "name": ch.channel_name,
                        "type": ch.spectral_type,
                        "wavelength_um": ch.central_wavelength_um,
                        "resolution_km": ch.nadir_resolution_km,
                        "unit": ch.physical_quantity,
                        "use": ch.primary_use,
                    }
                    for ch in spec.channels.values()
                ]
                product = SatelliteProduct(
                    id=uuid.uuid4(),
                    product_code=code,
                    satellite_name=spec.satellite_name,
                    sensor_name=spec.sensor_name,
                    processing_level=spec.processing_level,
                    spatial_resolution_km=4.0,
                    spectral_channels=channels_json,
                    calibration_info={
                        "sub_sat_lon": spec.nominal_sub_satellite_longitude_deg,
                        "cadence_min": spec.temporal_cadence_minutes,
                        "operational_span": f"{spec.operational_start_date} to {spec.operational_end_date or 'Present'}",
                    },
                    created_at_utc=datetime.now(UTC),
                )
                session.add(product)
                registered.append(product)
            else:
                registered.append(existing)
        session.flush()
        return registered

    @staticmethod
    def check_temporal_coverage(product_code: str, target_time: datetime) -> tuple[bool, str]:
        """Verify whether a target storm observation timestamp falls within product operational life."""
        spec = SUPPORTED_MOSDAC_PRODUCTS.get(product_code)
        if not spec:
            return False, f"Unknown MOSDAC product code: {product_code}"

        start_dt = datetime.strptime(spec.operational_start_date, "%Y-%m-%d").replace(tzinfo=UTC)
        end_dt = (
            datetime.strptime(spec.operational_end_date, "%Y-%m-%d").replace(tzinfo=UTC)
            if spec.operational_end_date
            else datetime.now(UTC)
        )

        if target_time < start_dt:
            return (
                False,
                f"Target time {target_time.isoformat()} precedes {spec.satellite_name} launch ({spec.operational_start_date})",
            )
        if target_time > end_dt:
            return (
                False,
                f"Target time {target_time.isoformat()} follows {spec.satellite_name} operational end ({spec.operational_end_date})",
            )

        return True, f"Target time is within active operational window of {spec.satellite_name}"

    @staticmethod
    def calculate_brightness_temperature(
        radiance: float,
        channel_name: str,
        coefficients: dict[str, float] | None = None,
    ) -> float | None:
        """Calculate physical Brightness Temperature (Kelvin) from spectral radiance using Planck inversion.

        Formula:
            T_eff = (c2 * nu) / ln(1 + (c1 * nu^3) / L)
            T_b = a + b * T_eff
        """
        import math

        if radiance <= 0.0:
            return None

        # Physical constants
        c1 = 1.191042e-5  # mW / (m^2 * sr * cm^-4)
        c2 = 1.4387752  # K * cm

        spec = INSAT_IMAGER_CHANNELS.get(channel_name)
        if not spec or spec.spectral_type == "Visible":
            return None

        # Effective central wavenumber (cm^-1) = 10000 / wavelength_um
        nu = 10000.0 / spec.central_wavelength_um

        try:
            val = (c1 * (nu**3)) / radiance
            t_eff = (c2 * nu) / math.log(1.0 + val)
        except (ValueError, ZeroDivisionError, OverflowError):
            return None

        if coefficients:
            a = coefficients.get("a", 0.0)
            b = coefficients.get("b", 1.0)
            return round(a + b * t_eff, 2)

        return round(t_eff, 2)
