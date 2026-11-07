"""Unit tests for TCIR HDF5 satellite adapter."""

from pathlib import Path

import numpy as np
import pytest

from vayumarg.satellite.tcir_adapter import EXPECTED_CHANNELS, TCIRAdapter

PILOT_FILE = Path("data/interim/tcir_nio_pilot.h5")


@pytest.mark.unit
def test_tcir_adapter_metadata_loading():
    """Verify that TCIRAdapter correctly parses the pilot HDF5 metadata table."""
    if not PILOT_FILE.is_file():
        pytest.skip(f"Pilot file missing: {PILOT_FILE}")

    adapter = TCIRAdapter(PILOT_FILE)
    df = adapter.load_metadata_table()

    assert len(df) == 12
    assert "sid" in df.columns
    assert "vmax" in df.columns
    assert "lat" in df.columns


@pytest.mark.unit
def test_tcir_adapter_frame_metadata_fields():
    """Verify individual frame metadata conversion and North Indian Ocean identification."""
    if not PILOT_FILE.is_file():
        pytest.skip(f"Pilot file missing: {PILOT_FILE}")

    adapter = TCIRAdapter(PILOT_FILE)
    meta = adapter.get_frame_metadata(0)

    assert meta.frame_index == 0
    assert meta.storm_name == "AMPHAN"
    assert meta.season_year == 2020
    assert meta.is_north_indian_ocean is True
    assert meta.vmax_knots == 30.0
    assert meta.latitude == 10.4
    assert meta.longitude == 86.6


@pytest.mark.unit
def test_tcir_adapter_lazy_channel_reading():
    """Verify lazy reading of multi-spectral image channels without full tensor load."""
    if not PILOT_FILE.is_file():
        pytest.skip(f"Pilot file missing: {PILOT_FILE}")

    adapter = TCIRAdapter(PILOT_FILE)
    channels = adapter.read_frame_channels(0, channels=["IR1", "WV"])

    assert "IR1" in channels
    assert "WV" in channels
    assert channels["IR1"].shape == (201, 201)
    assert channels["IR1"].dtype == np.float32

    # Physical brightness temperature bounds
    assert np.all(channels["IR1"] >= 180.0)
    assert np.all(channels["IR1"] <= 320.0)


@pytest.mark.unit
def test_tcir_adapter_nan_and_missingness_detection():
    """Verify that VIS nighttime missingness and PMW boundaries are captured."""
    if not PILOT_FILE.is_file():
        pytest.skip(f"Pilot file missing: {PILOT_FILE}")

    adapter = TCIRAdapter(PILOT_FILE)
    profile = adapter.generate_profile(sample_limit=12)

    assert profile.total_frames == 12
    assert profile.channels == EXPECTED_CHANNELS
    assert profile.channel_missing_percentages["IR1"] == 0.0
    assert profile.channel_missing_percentages["WV"] == 0.0
    # Nighttime visible frames should show 50% missingness
    assert profile.channel_missing_percentages["VIS"] == 50.0
    assert profile.channel_missing_percentages["PMW"] > 0.0
