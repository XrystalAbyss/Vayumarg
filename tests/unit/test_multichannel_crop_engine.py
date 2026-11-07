"""Unit tests for MultiChannelCropEngine, resampling, and calibration boundary handling."""

import numpy as np

from vayumarg.satellite.crop_engine import (
    CHANNEL_CONFIG,
    MultiChannelCropEngine,
    bilinear_resample_2d,
)


def test_bilinear_resample_identity() -> None:
    """Verify that resampling to the same shape is an exact identity operation."""
    arr = np.random.rand(50, 50).astype(np.float32)
    res = bilinear_resample_2d(arr, (50, 50))
    np.testing.assert_allclose(res, arr, atol=1e-6)


def test_bilinear_resample_upsampling() -> None:
    """Verify that 2x upsampling smoothly interpolates intermediate values."""
    # Simple linear ramp
    ramp_1d = np.linspace(0.0, 10.0, 5)
    ramp_2d = np.outer(ramp_1d, ramp_1d)

    # Upsample to 9x9 (2x resolution)
    upsampled = bilinear_resample_2d(ramp_2d, (9, 9))
    assert upsampled.shape == (9, 9)
    # Endpoints must match exactly
    assert np.isclose(upsampled[0, 0], ramp_2d[0, 0])
    assert np.isclose(upsampled[-1, -1], ramp_2d[-1, -1])
    # Midpoint must match linear interpolation
    assert np.isclose(upsampled[4, 4], ramp_2d[2, 2])


def test_channel_config_and_lut_clamping_bounds() -> None:
    """Verify channel configuration constants and lower boundary definitions."""
    assert "TIR-1" in CHANNEL_CONFIG
    assert "WV" in CHANNEL_CONFIG
    assert "TIR-2" in CHANNEL_CONFIG
    assert "MIR" in CHANNEL_CONFIG

    # TIR-1 native resolution is 4 km; WV native resolution is 8 km
    assert CHANNEL_CONFIG["TIR-1"]["native_res_km"] == 4.0
    assert CHANNEL_CONFIG["WV"]["native_res_km"] == 8.0

    # Space fill value is 1023 across all 10-bit channels
    for ch_cfg in CHANNEL_CONFIG.values():
        assert ch_cfg["fill_value"] == 1023
        assert ch_cfg["clamped_count_min"] >= 900


def test_crop_engine_physical_extent_calculation() -> None:
    """Verify that physical extent translates to correct pixel dimensions."""
    engine_800 = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    assert engine_800.target_pixels == 201
    assert engine_800.target_shape == (201, 201)

    engine_1000 = MultiChannelCropEngine(extent_km=1000.0, target_resolution_km=4.0)
    assert engine_1000.target_pixels == 251
    assert engine_1000.target_shape == (251, 251)


def test_bilinear_resample_with_valid_mask_prevents_contamination() -> None:
    """Verify that normalized bilinear interpolation prevents fill values from contaminating valid pixels."""
    # 2x2 grid: top-left, top-right, bottom-left are 250.0 K; bottom-right is fill value 999.0 K
    arr = np.array([[250.0, 250.0], [250.0, 999.0]], dtype=float)
    mask = np.array([[True, True], [True, False]], dtype=bool)

    # Upsample to 3x3
    res = bilinear_resample_2d(arr, (3, 3), valid_mask=mask)

    # Center pixel (1, 1) has 3 valid neighbors (all 250.0) and 1 invalid neighbor (999.0).
    # Re-normalized valid weighting must result in exactly 250.0 K, NOT an average with 999.0!
    assert np.isclose(res[1, 1], 250.0)
    # Valid top-left corner must be exactly 250.0
    assert np.isclose(res[0, 0], 250.0)
    # The invalid bottom-right corner had weight 1.0 on invalid pixel -> must be NaN
    assert np.isnan(res[2, 2])


def test_bilinear_resample_nan_propagation_and_no_zero_substitution() -> None:
    """Verify that completely invalid regions evaluate to NaN and are never silently zero-substituted."""
    arr = np.array([[np.nan, np.nan], [np.nan, 220.0]], dtype=float)
    res = bilinear_resample_2d(arr, (4, 4))

    # Top-left region has no valid neighbors -> must be NaN, not 0.0
    assert np.isnan(res[0, 0])
    assert np.isnan(res[0, 1])
    assert not np.isnan(res[-1, -1])
    assert np.isclose(res[-1, -1], 220.0)
