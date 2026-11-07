"""Unit tests for SatelliteImageService."""

import pytest

from vayumarg.satellite.service import get_satellite_service


def test_list_authentic_crops():
    """Verify service lists all 4 authentic crops."""
    service = get_satellite_service()
    crops = service.list_authentic_crops()
    names = {c.storm_name for c in crops}
    assert {"REMAL", "DANA", "AMPHAN", "BIPARJOY"}.issubset(names)


def test_channel_array_loading_and_shape():
    """Verify loading real 201x201 multichannel crops from HDF5 containers."""
    service = get_satellite_service()
    for storm in ["REMAL", "DANA", "AMPHAN", "BIPARJOY"]:
        for ch in ["TIR-1", "WV", "TIR-2", "MIR"]:
            arr, valid, clamped = service.load_channel_array(storm, ch)
            assert arr.shape == (201, 201), f"Expected (201, 201) for {storm} {ch}, got {arr.shape}"
            assert valid.shape == (201, 201)
            assert clamped.shape == (201, 201)
            # Physical Kelvin check: temperatures must be > 170 K and < 350 K
            valid_temps = arr[valid]
            assert len(valid_temps) > 0
            assert valid_temps.min() >= 170.0
            assert valid_temps.max() <= 350.0


def test_channel_switching_and_preview_caching():
    """Verify fast preview generation and subsequent cache hit."""
    service = get_satellite_service()
    # 1. First fetch: renders preview
    preview_tir1 = service.get_channel_preview("REMAL", "TIR-1", colormap="thermal_ir")
    assert len(preview_tir1) > 0

    # 2. Channel switch to WV
    preview_wv = service.get_channel_preview("REMAL", "WV", colormap="thermal_ir")
    assert len(preview_wv) > 0
    assert preview_tir1 != preview_wv  # Different channels must yield different imagery

    # 3. Second fetch of TIR-1: cache hit
    preview_cached = service.get_channel_preview("REMAL", "TIR-1", colormap="thermal_ir")
    assert preview_tir1 == preview_cached


def test_missing_channel_raises_value_error():
    """Verify requesting an unsupported channel raises ValueError."""
    service = get_satellite_service()
    with pytest.raises(ValueError, match="Channel 'VIS_1KM' unavailable"):
        service.load_channel_array("REMAL", "VIS_1KM")


def test_missing_crop_raises_key_error():
    """Verify requesting a non-existent storm raises KeyError."""
    service = get_satellite_service()
    with pytest.raises(KeyError, match="Authentic satellite crop not found"):
        service.get_crop_provenance("FAKE_CYCLONE_999")
