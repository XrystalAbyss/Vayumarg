"""Unit tests for quantitative scientific satellite image analytics."""

import numpy as np
import pytest

from vayumarg.satellite.analytics import (
    COLD_CLOUD_THRESHOLDS,
    RADIAL_BINS_KM,
    SatelliteImageAnalyticsEngine,
)


def test_valid_and_missing_fractions():
    """Verify exact valid and missing pixel fraction calculations."""
    temps = np.full((10, 10), 250.0)
    valid_mask = np.ones((10, 10), dtype=bool)
    valid_mask[:2, :] = False  # 20 pixels invalid

    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
        valid_mask=valid_mask,
    )
    assert an.total_pixels == 100
    assert an.valid_pixels == 80
    assert an.missing_pixels == 20
    assert an.valid_fraction == 0.8
    assert an.missing_fraction == 0.2


def test_clamping_fraction_and_non_clamped_minimum():
    """Verify lower LUT clamping detection distinguishes boundary limits from real physical temps."""
    temps = np.full((10, 10), 220.0)
    # Set 10 pixels to LUT boundary (179.86 K)
    temps[0, :10] = 179.86
    # Set one non-clamped minimum
    temps[1, 0] = 185.50

    clamped_mask = np.zeros((10, 10), dtype=bool)
    clamped_mask[0, :10] = True

    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
        clamped_mask=clamped_mask,
        lut_boundary_kelvin=179.86,
    )
    assert an.clamped_pixels == 10
    assert an.clamped_fraction == 0.10
    assert an.is_lut_censored is True
    assert an.min_tb_k == 179.86
    assert an.min_non_clamped_tb_k == 185.50


def test_temperature_percentiles():
    """Verify percentiles and statistical moments."""
    temps = np.linspace(180.0, 300.0, 100).reshape(10, 10)
    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
    )
    assert an.min_tb_k == 180.0
    assert an.max_tb_k == 300.0
    assert "p10" in an.percentiles_tb_k
    assert "p50" in an.percentiles_tb_k
    assert "p90" in an.percentiles_tb_k
    assert an.percentiles_tb_k["p10"] < an.percentiles_tb_k["p50"] < an.percentiles_tb_k["p90"]


def test_cold_cloud_thresholds_justification():
    """Verify cold-cloud fractions at explicitly defined thresholds with scientific justifications."""
    temps = np.full((10, 10), 250.0)
    # 20 pixels under 240K, 15 under 220K, 10 under 200K, 5 under 190K
    temps[0:2, :] = 230.0  # 20 pixels < 240K
    temps[0, :5] = 210.0  # 5 pixels < 220K
    temps[1, :5] = 195.0  # 5 pixels < 200K
    temps[1, :2] = 185.0  # 2 pixels < 190K

    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
    )
    assert len(an.cold_cloud_fractions) == len(COLD_CLOUD_THRESHOLDS)
    f240 = [cf for cf in an.cold_cloud_fractions if cf.threshold_k == 240.0][0]
    f220 = [cf for cf in an.cold_cloud_fractions if cf.threshold_k == 220.0][0]
    f200 = [cf for cf in an.cold_cloud_fractions if cf.threshold_k == 200.0][0]
    f190 = [cf for cf in an.cold_cloud_fractions if cf.threshold_k == 190.0][0]

    assert (
        f240.fraction_of_valid
        >= f220.fraction_of_valid
        >= f200.fraction_of_valid
        >= f190.fraction_of_valid
    )
    assert "anvil" in f240.scientific_justification.lower()
    assert "dvorak" in f220.scientific_justification.lower()
    assert "overshooting" in f190.scientific_justification.lower()


def test_radial_profile_computation():
    """Verify radial ring temperature profiling from cyclone eye center."""
    temps = np.full((201, 201), 220.0)
    # Put a warm eye at center
    temps[98:103, 98:103] = 270.0

    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
        grid_spacing_km=4.0,
    )
    assert len(an.radial_profile) == len(RADIAL_BINS_KM)
    eye_bin = an.radial_profile[0]
    assert eye_bin.bin_name.startswith("0-25 km")
    assert eye_bin.valid_pixel_count > 0
    # Eye mean should be warmer than outer rings
    outer_bin = an.radial_profile[-1]
    assert eye_bin.mean_tb_k > outer_bin.mean_tb_k


def test_spatial_gradient_statistics():
    """Verify 2D central difference gradient magnitude statistics in K/km."""
    # Linear ramp along x: 10 K change per pixel (4 km) -> 2.5 K/km
    x = np.arange(20) * 10.0
    temps = np.tile(x, (20, 1)).astype(float)

    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
        grid_spacing_km=4.0,
    )
    assert an.gradient_statistics.mean_k_per_km == pytest.approx(2.5, abs=0.01)
    assert an.gradient_statistics.median_k_per_km == pytest.approx(2.5, abs=0.01)


def test_cloud_field_symmetry_and_disclaimer():
    """Verify azimuthal asymmetry metrics and mandatory scientific disclaimer."""
    temps = np.full((101, 101), 220.0)
    # Make NE quadrant colder
    temps[:50, 51:] = 190.0

    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="TIR-1",
        temps_k=temps,
        grid_spacing_km=4.0,
    )
    symm = an.symmetry_metrics
    assert "NE" in symm.quadrant_means_k
    assert symm.quadrant_means_k["NE"] < symm.quadrant_means_k["SW"]
    assert symm.azimuthal_asymmetry_index > 0.0
    # Mandatory disclaimer must be present
    assert (
        "does not represent a calibrated cyclone intensity predictor" in symm.scientific_disclaimer
    )


def test_insat_3ds_wv_resolution_safety():
    """Verify INSAT-3DS WV channel explicitly distinguishes 8km native resolution from 4km delivered grid."""
    temps = np.full((10, 10), 240.0)
    an = SatelliteImageAnalyticsEngine.compute_channel_analytics(
        channel_name="WV",
        temps_k=temps,
        grid_spacing_km=4.0,
        native_resolution_km=8.0,
        delivered_resolution_km=4.0,
        satellite_name="INSAT-3DS",
    )
    assert an.resolution_lineage.native_instrument_resolution_km == 8.0
    assert an.resolution_lineage.delivered_product_grid_spacing_km == 4.0
    assert an.resolution_lineage.effective_resolution_km == 8.0
    assert (
        "must not be treated as 4.0 km independent physical sensor resolution"
        in an.resolution_lineage.scientific_caveat
    )
