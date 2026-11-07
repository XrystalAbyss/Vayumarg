"""Update DANA crop quality_control_flags with multi-dimensional model eligibility and sensor resolution metadata."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import SatelliteProcessedCrop


def main():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        crop = s.execute(
            select(SatelliteProcessedCrop).where(SatelliteProcessedCrop.storage_uri.like("%DANA%"))
        ).scalar_one()

        qc = dict(crop.quality_control_flags or {})

        # Multi-dimensional model eligibility
        qc["model_eligibility"] = {
            "general_atmospheric_research": True,
            "post_landfall_weakening_analysis": True,
            "agency_conditioned_jtwc_intensity": True,
            "primary_imd_category_classification": False,
            "primary_imd_wind_intensity_regression": False,
            "ineligibility_reasons": [
                "Primary IMD best-track cyclonic classification terminated at 18:00 UTC (Depression, 25 kt). By 00:00 UTC 26 Oct 2024, IMD documented DANA weakened into a Well Marked Low Pressure Area (WML < 17 kt), ending official cyclone categorization."
            ],
        }

        # Sensor resolution metadata for INSAT-3DS channels
        qc["sensor_resolution_audit"] = {
            "TIR-1": {
                "native_instrument_resolution_km": 4.0,
                "delivered_product_grid_spacing_km": 4.0,
                "target_crop_grid_spacing_km": 4.0,
                "effective_resolution_km": 4.0,
                "resampling_method": "native/none",
                "source_documentation": "MOSDAC INSAT-3DS Operational Products V1 & HDF5 IMG_TIR1 metadata (resolution=4.0km)",
            },
            "WV": {
                "native_instrument_resolution_km": 8.0,
                "delivered_product_grid_spacing_km": 4.0,
                "target_crop_grid_spacing_km": 4.0,
                "effective_resolution_km": 8.0,
                "resampling_method": "delivered L1B co-registered grid (no additional interpolation)",
                "source_documentation": "MOSDAC INSAT-3DS Operational Products V1 & HDF5 IMG_WV metadata (resolution=8.0km)",
            },
            "TIR-2": {
                "native_instrument_resolution_km": 4.0,
                "delivered_product_grid_spacing_km": 4.0,
                "target_crop_grid_spacing_km": 4.0,
                "effective_resolution_km": 4.0,
                "resampling_method": "native/none",
                "source_documentation": "MOSDAC INSAT-3DS Operational Products V1 & HDF5 IMG_TIR2 metadata (resolution=4.0km)",
            },
            "MIR": {
                "native_instrument_resolution_km": 4.0,
                "delivered_product_grid_spacing_km": 4.0,
                "target_crop_grid_spacing_km": 4.0,
                "effective_resolution_km": 4.0,
                "resampling_method": "native/none",
                "source_documentation": "MOSDAC INSAT-3DS Operational Products V1 & HDF5 IMG_MIR metadata (resolution=4.0km)",
            },
        }

        # Radiometric clamping audit
        qc["radiometric_audit"] = {
            "total_pixels": 40401,
            "valid_pixels": 40400,
            "fill_pixels": 1,
            "clamped_pixels_on_valid": 0,
            "clamping_rate_on_valid": 0.0,
            "sensor_floor_kelvin": 180.0,
        }

        crop.quality_control_flags = qc
        s.commit()
        print("Updated DANA crop quality_control_flags successfully.")
        print(f"Crop ID: {crop.id}")
        print("Keys in updated QC flags:", list(crop.quality_control_flags.keys()))


if __name__ == "__main__":
    main()
