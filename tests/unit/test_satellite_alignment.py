"""Unit tests for satellite and best-track spatiotemporal alignment logic."""

import pytest

from vayumarg.satellite.alignment import (
    SatelliteTrackAligner,
    calculate_haversine_distance_km,
)


@pytest.mark.unit
def test_haversine_distance_calculation():
    """Verify great-circle distance calculation between known coordinate pairs."""
    # Distance between Chennai (13.0827N, 80.2707E) and Kolkata (22.5726N, 88.3639E) is ~1366 km
    dist = calculate_haversine_distance_km(13.0827, 80.2707, 22.5726, 88.3639)
    assert 1350.0 <= dist <= 1380.0

    # Distance between identical points is 0.0
    assert calculate_haversine_distance_km(15.0, 85.0, 15.0, 85.0) == 0.0


@pytest.mark.unit
def test_aligner_tolerance_boundaries():
    """Verify aligner configuration limits."""
    aligner = SatelliteTrackAligner(max_temporal_offset_minutes=30.0, max_spatial_offset_km=100.0)

    assert aligner.max_temporal_offset == 30.0
    assert aligner.max_spatial_offset == 100.0
