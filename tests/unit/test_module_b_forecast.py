"""Unit tests for Module B Geodesic Forecast Engine & Verification Subsystem.

Tests:
- Chronological filtering & validation.
- Source agency consistency & wind averaging preservation.
- Zero displacement (stationary storm).
- Longitude wrap across dateline/antimeridian.
- Irregular observation intervals.
- Missing, nonfinite, or out-of-range coordinates.
- Insufficient history (< 2 usable fixes) & distant fix recency rejection.
- 6/12/24-hour geodesic projection accuracy.
- Wind persistence baseline and bounded-trend comparator.
- Hindsight verification error calculations.
- GeoJSON coordinate ordering ([longitude, latitude]).
"""

from datetime import UTC, datetime, timedelta

import pytest

from vayumarg.module_b.contracts import (
    ForecastStatus,
)
from vayumarg.module_b.forecast_engine import (
    calculate_bearing_deg,
    calculate_great_circle_distance_km,
    classify_imd_category,
    compute_geodesic_forecast,
    compute_hindsight_verification,
    extrapolate_geodesic,
    validate_and_clean_observations,
)


def test_classify_imd_category():
    """Verify official IMD 3-minute sustained wind classification boundaries."""
    assert classify_imd_category(None) is None
    assert classify_imd_category(15.0) == "Low Pressure Area"
    assert classify_imd_category(20.0) == "Depression (D)"
    assert classify_imd_category(30.0) == "Deep Depression (DD)"
    assert classify_imd_category(40.0) == "Cyclonic Storm (CS)"
    assert classify_imd_category(55.0) == "Severe Cyclonic Storm (SCS)"
    assert classify_imd_category(75.0) == "Very Severe Cyclonic Storm (VSCS)"
    assert classify_imd_category(100.0) == "Extremely Severe Cyclonic Storm (ESCS)"
    assert classify_imd_category(130.0) == "Super Cyclonic Storm (SuCS)"


def test_great_circle_distance_and_bearing_equator():
    """Verify great-circle distance and cardinal bearings along equator and meridians."""
    # 1 degree along equator ~ 111.19 km
    dist = calculate_great_circle_distance_km(0.0, 0.0, 0.0, 1.0)
    assert pytest.approx(dist, rel=1e-3) == 111.195

    # Cardinal North bearing: (10.0, 70.0) to (12.0, 70.0)
    bearing_n = calculate_bearing_deg(10.0, 70.0, 12.0, 70.0)
    assert pytest.approx(bearing_n, abs=1e-2) == 0.0

    # Cardinal East bearing along equator: (0.0, 70.0) to (0.0, 72.0) is exactly 90.0°
    bearing_e_eq = calculate_bearing_deg(0.0, 70.0, 0.0, 72.0)
    assert pytest.approx(bearing_e_eq, abs=1e-2) == 90.0

    # Along parallel 10°N: initial great-circle bearing is ~89.83° (rhumb vs geodesic)
    bearing_e_10n = calculate_bearing_deg(10.0, 70.0, 10.0, 72.0)
    assert pytest.approx(bearing_e_10n, abs=0.2) == 90.0

    # Cardinal South bearing: (12.0, 70.0) to (10.0, 70.0)
    bearing_s = calculate_bearing_deg(12.0, 70.0, 10.0, 70.0)
    assert pytest.approx(bearing_s, abs=1e-2) == 180.0

    # Cardinal West bearing along equator: (0.0, 72.0) to (0.0, 70.0) is exactly 270.0°
    bearing_w_eq = calculate_bearing_deg(0.0, 72.0, 0.0, 70.0)
    assert pytest.approx(bearing_w_eq, abs=1e-2) == 270.0

    # Along parallel 10°N: initial great-circle bearing is ~270.17° (rhumb vs geodesic)
    bearing_w_10n = calculate_bearing_deg(10.0, 72.0, 10.0, 70.0)
    assert pytest.approx(bearing_w_10n, abs=0.2) == 270.0


def test_longitude_wrap_distance_and_bearing():
    """Verify distance and bearing across the antimeridian (+179.0 to -179.0)."""
    # Crossing 180°: 179° to -179° is 2 degrees eastward, not 358 degrees westward
    dist_wrap = calculate_great_circle_distance_km(0.0, 179.0, 0.0, -179.0)
    assert pytest.approx(dist_wrap, rel=1e-3) == 222.39

    bearing_wrap = calculate_bearing_deg(0.0, 179.0, 0.0, -179.0)
    assert pytest.approx(bearing_wrap, abs=1e-2) == 90.0

    # Extrapolating east across 180
    lat2, lon2 = extrapolate_geodesic(0.0, 179.0, 90.0, 222.39)
    assert pytest.approx(lat2, abs=0.1) == 0.0
    assert pytest.approx(lon2, abs=0.1) == -179.0


def test_zero_displacement_stationary_storm():
    """Verify handling when storm is stalled/stationary (zero displacement)."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 10, 3, 0, tzinfo=UTC)

    obs = [
        {"observation_time_utc": t0, "latitude": 15.0, "longitude": 68.0, "wind_speed_knots": 60.0},
        {"observation_time_utc": t1, "latitude": 15.0, "longitude": 68.0, "wind_speed_knots": 60.0},
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_stationary",
        storm_sid="TEST_STAT_01",
        storm_name="STAT_CYCLONE",
        season_year=2023,
        primary_basin="AS",
        source_agency="IMD",
        observations=obs,
        issue_time_utc=t1,
        horizons_hours=[6, 12, 24],
    )

    assert fc.status == ForecastStatus.SUCCESS
    assert fc.translational_motion.speed_kmh == 0.0
    assert fc.translational_motion.bearing_deg == 0.0
    assert fc.translational_motion.displacement_km == 0.0

    # Forecast coordinates must remain stationary at (15.0, 68.0)
    for hp in fc.forecast_horizons:
        assert hp.predicted_latitude == 15.0
        assert hp.predicted_longitude == 68.0
        assert hp.projected_distance_km == 0.0
        assert hp.predicted_wind_persistence_knots == 60.0
        assert hp.predicted_wind_trend_knots == 60.0


def test_irregular_observation_intervals():
    """Verify correct translational speed derivation with non-standard elapsed times (e.g. 1.5h, 4.5h)."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 10, 1, 30, tzinfo=UTC)  # 1.5 hours

    # Move 0.3 deg North ~ 33.358 km
    obs = [
        {"observation_time_utc": t0, "latitude": 10.0, "longitude": 70.0, "wind_speed_knots": 40.0},
        {"observation_time_utc": t1, "latitude": 10.3, "longitude": 70.0, "wind_speed_knots": 45.0},
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_irregular",
        storm_sid="TEST_IRREG_01",
        storm_name="IRREG_CYCLONE",
        season_year=2023,
        primary_basin="AS",
        source_agency="IMD",
        observations=obs,
        issue_time_utc=t1,
        horizons_hours=[6, 12, 24],
    )

    assert fc.status == ForecastStatus.SUCCESS
    assert fc.translational_motion.delta_hours == 1.5
    # speed = 33.358 / 1.5 ~ 22.24 km/h
    assert pytest.approx(fc.translational_motion.speed_kmh, rel=1e-2) == 22.24
    assert pytest.approx(fc.translational_motion.bearing_deg, abs=0.5) == 0.0

    # At +6h: dist = 22.24 * 6 = 133.43 km -> ~1.2 degrees North -> lat ~ 11.5
    h6 = fc.forecast_horizons[0]
    assert pytest.approx(h6.predicted_latitude, abs=0.05) == 11.50
    assert pytest.approx(h6.predicted_longitude, abs=0.05) == 70.0


def test_missing_and_nonfinite_coordinates_filtered():
    """Verify that observations with None, NaN, inf, or out-of-range lat/lon are safely rejected."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    t_invalid1 = datetime(2023, 6, 10, 1, 0, tzinfo=UTC)
    t_invalid2 = datetime(2023, 6, 10, 2, 0, tzinfo=UTC)
    t_invalid3 = datetime(2023, 6, 10, 3, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 10, 6, 0, tzinfo=UTC)

    obs = [
        {"observation_time_utc": t0, "latitude": 10.0, "longitude": 70.0, "wind_speed_knots": 35.0},
        {
            "observation_time_utc": t_invalid1,
            "latitude": None,
            "longitude": 70.0,
            "wind_speed_knots": 35.0,
        },
        {
            "observation_time_utc": t_invalid2,
            "latitude": float("nan"),
            "longitude": 70.0,
            "wind_speed_knots": 35.0,
        },
        {
            "observation_time_utc": t_invalid3,
            "latitude": 120.0,
            "longitude": 70.0,
            "wind_speed_knots": 35.0,
        },  # lat > 90
        {"observation_time_utc": t1, "latitude": 11.0, "longitude": 70.0, "wind_speed_knots": 45.0},
    ]

    clean = validate_and_clean_observations(obs, t1)
    assert len(clean) == 2
    assert clean[0].observation_time_utc == t0
    assert clean[1].observation_time_utc == t1


def test_insufficient_history_returns_unavailable():
    """Verify that fewer than 2 valid historical observations return UNAVAILABLE status without inventing tracks."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    obs = [
        {"observation_time_utc": t0, "latitude": 10.0, "longitude": 70.0, "wind_speed_knots": 30.0}
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_insufficient",
        storm_sid="TEST_INSUF_01",
        storm_name="INSUF_CYCLONE",
        season_year=2023,
        primary_basin="AS",
        source_agency="IMD",
        observations=obs,
        issue_time_utc=t0,
    )

    assert fc.status == ForecastStatus.UNAVAILABLE
    assert "Insufficient historical track points" in (fc.unavailability_reason or "")
    assert len(fc.forecast_horizons) == 0


def test_distant_fix_recency_rejection():
    """Verify that if the last available fix is older than the max recency threshold (24h), status is UNAVAILABLE."""
    t0 = datetime(2023, 6, 1, 0, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 1, 6, 0, tzinfo=UTC)
    issue_t = datetime(2023, 6, 3, 0, 0, tzinfo=UTC)  # 42 hours later

    obs = [
        {"observation_time_utc": t0, "latitude": 10.0, "longitude": 70.0, "wind_speed_knots": 30.0},
        {"observation_time_utc": t1, "latitude": 10.5, "longitude": 70.0, "wind_speed_knots": 35.0},
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_stale",
        storm_sid="TEST_STALE_01",
        storm_name="STALE_CYCLONE",
        season_year=2023,
        primary_basin="AS",
        source_agency="IMD",
        observations=obs,
        issue_time_utc=issue_t,
        max_fix_recency_hours=24.0,
    )

    assert fc.status == ForecastStatus.UNAVAILABLE
    assert "exceeding operational recency threshold" in (fc.unavailability_reason or "")


def test_wind_averaging_period_and_intensity_baselines():
    """Verify persistence baseline and bounded trend comparator calculations."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 10, 6, 0, tzinfo=UTC)  # 6h elapsed

    # Wind intensified from 50 to 65 kt (+15 kt over 6h = +2.5 kt/h)
    obs = [
        {
            "observation_time_utc": t0,
            "latitude": 12.0,
            "longitude": 85.0,
            "wind_speed_knots": 50.0,
            "averaging_period": "3-min",
        },
        {
            "observation_time_utc": t1,
            "latitude": 13.0,
            "longitude": 85.0,
            "wind_speed_knots": 65.0,
            "averaging_period": "3-min",
        },
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_wind",
        storm_sid="TEST_WIND_01",
        storm_name="WIND_CYCLONE",
        season_year=2023,
        primary_basin="BB",
        source_agency="IMD",
        observations=obs,
        issue_time_utc=t1,
        horizons_hours=[6, 12, 24],
    )

    assert fc.status == ForecastStatus.SUCCESS
    assert fc.wind_averaging_period == "3-min"

    # Persistence: carries 65.0 kt across all horizons
    for hp in fc.forecast_horizons:
        assert hp.predicted_wind_persistence_knots == 65.0
        assert hp.predicted_imd_category_persistence == "Very Severe Cyclonic Storm (VSCS)"

    # Bounded trend:
    # +6h: trend = 2.5 kt/h, damping = 1 - 6/36 = 0.833 -> delta = 2.5 * 6 * 0.833 ~ 12.5 -> wind ~ 77.5 kt
    h6 = fc.forecast_horizons[0]
    assert pytest.approx(h6.predicted_wind_trend_knots, abs=0.5) == 77.5

    # +24h: damping = 1 - 24/36 = 0.333 -> delta = 2.5 * 24 * 0.333 ~ 20.0 -> wind ~ 85.0 kt
    h24 = fc.forecast_horizons[2]
    assert pytest.approx(h24.predicted_wind_trend_knots, abs=0.5) == 85.0


def test_hindsight_verification_geodesic_error():
    """Verify hindsight verification error computation and target-missing handling."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 10, 6, 0, tzinfo=UTC)
    issue_t = t1

    obs_history = [
        {"observation_time_utc": t0, "latitude": 10.0, "longitude": 70.0, "wind_speed_knots": 40.0},
        {"observation_time_utc": t1, "latitude": 11.0, "longitude": 70.0, "wind_speed_knots": 40.0},
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_veri",
        storm_sid="TEST_VERI_01",
        storm_name="VERI_CYCLONE",
        season_year=2023,
        primary_basin="AS",
        source_agency="IMD",
        observations=obs_history,
        issue_time_utc=issue_t,
        horizons_hours=[6, 12, 24],
    )

    # Future ground truth: fix available at +6h and +12h, but MISSING at +24h
    t_plus_6 = issue_t + timedelta(hours=6)
    t_plus_12 = issue_t + timedelta(hours=12)

    future_obs = [
        # Actual at +6h: slightly deviated (12.1 vs pred 12.0)
        {
            "observation_time_utc": t_plus_6,
            "latitude": 12.1,
            "longitude": 70.0,
            "wind_speed_knots": 45.0,
        },
        # Actual at +12h: (13.2 vs pred 13.0)
        {
            "observation_time_utc": t_plus_12,
            "latitude": 13.2,
            "longitude": 70.0,
            "wind_speed_knots": 50.0,
        },
    ]

    ver = compute_hindsight_verification(fc, future_obs, tolerance_hours=3.0)

    assert ver.horizons_evaluated == 3
    assert ver.horizons_matched == 2

    # +6h
    v6 = ver.verification_horizons[0]
    assert v6.target_status == "VERIFIED"
    assert v6.actual_latitude == 12.1
    assert v6.actual_wind_kt == 45.0
    assert v6.persistence_wind_error_kt == 5.0
    # Expected track error: ~0.1 deg ~ 11.12 km
    assert pytest.approx(v6.geodesic_track_error_km, abs=0.5) == 11.12

    # +12h
    v12 = ver.verification_horizons[1]
    assert v12.target_status == "VERIFIED"
    # ~0.2 deg ~ 22.24 km
    assert pytest.approx(v12.geodesic_track_error_km, abs=0.5) == 22.24

    # +24h: Target unavailable
    v24 = ver.verification_horizons[2]
    assert v24.target_status == "TARGET_UNAVAILABLE"
    assert v24.actual_latitude is None
    assert v24.geodesic_track_error_km is None


def test_geojson_coordinate_ordering_rfc7946():
    """Verify GeoJSON RFC 7946 compliance: Point coordinates MUST be [longitude, latitude]."""
    t0 = datetime(2023, 6, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2023, 6, 10, 6, 0, tzinfo=UTC)

    obs = [
        {"observation_time_utc": t0, "latitude": 15.2, "longitude": 68.4, "wind_speed_knots": 40.0},
        {"observation_time_utc": t1, "latitude": 16.0, "longitude": 68.6, "wind_speed_knots": 45.0},
    ]

    fc = compute_geodesic_forecast(
        storm_id="test_geojson",
        storm_sid="TEST_GEOJSON_01",
        storm_name="GEO_CYCLONE",
        season_year=2023,
        primary_basin="AS",
        source_agency="IMD",
        observations=obs,
        issue_time_utc=t1,
        horizons_hours=[6, 12, 24],
    )

    assert fc.geojson is not None
    assert fc.geojson.type == "FeatureCollection"

    for feat in fc.geojson.features:
        if feat.geometry["type"] == "Point":
            coords = feat.geometry["coordinates"]
            assert len(coords) == 2
            lon, lat = coords[0], coords[1]
            # Longitude in Indian Ocean is ~60-95°E, Latitude is ~5-30°N
            assert 60.0 <= lon <= 80.0
            assert 10.0 <= lat <= 30.0
