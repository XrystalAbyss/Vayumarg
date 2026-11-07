"""Unit tests for ISRO MOSDAC product specifications and calibration physics."""

from datetime import UTC, datetime

import pytest

from vayumarg.satellite.mosdac_adapter import (
    INSAT_IMAGER_CHANNELS,
    SUPPORTED_MOSDAC_PRODUCTS,
    MOSDACAdapter,
)


@pytest.mark.unit
def test_mosdac_supported_products_registry():
    """Verify registry contains INSAT-3DS, 3DR, and 3D with correct operational metadata."""
    products = MOSDACAdapter.get_supported_products()
    codes = {p["product_code"] for p in products}

    assert "3SIMG_L1B_STD" in codes
    assert "3RIMG_L1B_STD" in codes
    assert "3DIMG_L1B_STD" in codes

    insat3ds = SUPPORTED_MOSDAC_PRODUCTS["3SIMG_L1B_STD"]
    assert insat3ds.satellite_name == "INSAT-3DS"
    assert insat3ds.temporal_cadence_minutes == 15
    assert insat3ds.nominal_sub_satellite_longitude_deg == 74.0


@pytest.mark.unit
def test_mosdac_imager_channel_resolutions():
    """Verify nadir ground resolutions across spectral bands."""
    assert INSAT_IMAGER_CHANNELS["VIS"].nadir_resolution_km == 1.0
    assert INSAT_IMAGER_CHANNELS["SWIR"].nadir_resolution_km == 1.0
    assert INSAT_IMAGER_CHANNELS["MIR"].nadir_resolution_km == 4.0
    assert INSAT_IMAGER_CHANNELS["WV"].nadir_resolution_km == 8.0
    assert INSAT_IMAGER_CHANNELS["TIR-1"].nadir_resolution_km == 4.0
    assert INSAT_IMAGER_CHANNELS["TIR-2"].nadir_resolution_km == 4.0


@pytest.mark.unit
def test_mosdac_temporal_coverage_validation():
    """Verify temporal coverage logic prevents matching storms outside sensor lifetime."""
    # Cyclone DANA (October 2024) -> Valid on INSAT-3DS
    dana_time = datetime(2024, 10, 24, 12, 0, tzinfo=UTC)
    is_valid, _ = MOSDACAdapter.check_temporal_coverage("3SIMG_L1B_STD", dana_time)
    assert is_valid is True

    # Cyclone AMPHAN (May 2020) -> Invalid on INSAT-3DS (precedes launch)
    amphan_time = datetime(2020, 5, 18, 12, 0, tzinfo=UTC)
    is_valid, reason = MOSDACAdapter.check_temporal_coverage("3SIMG_L1B_STD", amphan_time)
    assert is_valid is False
    assert "precedes INSAT-3DS launch" in reason

    # Cyclone AMPHAN (May 2020) -> Valid on INSAT-3D
    is_valid_3d, _ = MOSDACAdapter.check_temporal_coverage("3DIMG_L1B_STD", amphan_time)
    assert is_valid_3d is True


@pytest.mark.unit
def test_mosdac_planck_brightness_temperature_inversion():
    """Verify physical brightness temperature calculation from spectral radiance."""
    # Nominal radiance for TIR-1 (~10.8 um) around 280 K is ~82.0 mW/(m^2*sr*cm^-1)
    radiance = 82.0
    tb = MOSDACAdapter.calculate_brightness_temperature(radiance, "TIR-1")

    assert tb is not None
    assert 275.0 <= tb <= 285.0

    # Non-physical radiance should return None
    assert MOSDACAdapter.calculate_brightness_temperature(-1.0, "TIR-1") is None
    assert MOSDACAdapter.calculate_brightness_temperature(10.0, "VIS") is None
