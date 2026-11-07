"""Integration tests for Module B Forecast Engine against PostgreSQL vayumarg database.

Tests:
1. Ground truth leakage protection regression test: deliberately injects future observations
   and demonstrates unchanged forecast results.
2. Source agency consistency & chronological filtering.
3. Database read-only invariant: zero mutations during forecast and verification.
4. Three historical visual demonstration cases: BIPARJOY, AMPHAN, and REMAL.
5. FastAPI operational endpoint integration and JSON/GeoJSON serialization.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select

from vayumarg.api.server import app
from vayumarg.database.engine import get_db_session, get_default_engine
from vayumarg.database.schema import SourceAsset, Storm, StormAlias, TrackObservation
from vayumarg.module_b.contracts import ForecastStatus
from vayumarg.module_b.forecast_engine import (
    generate_forecast_from_db,
    resolve_storm_in_database,
    verify_forecast_from_db,
)


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


def test_ground_truth_leakage_protection_regression():
    """REGRESSION TEST: Deliberately inject future observations into database and verify forecast is UNCHANGED.

    Mandatory Ground Truth Leakage Protection verification.
    """
    engine = get_default_engine()
    issue_time = datetime(2023, 6, 11, 6, 0, tzinfo=UTC)
    storm_sid = "2023156N10067"  # BIPARJOY

    # Step 1: Run baseline forecast strictly up to issue_time
    with get_db_session(engine) as session:
        baseline_fc = generate_forecast_from_db(
            session=session,
            storm_identifier=storm_sid,
            agency="IMD",
            issue_time_utc=issue_time,
            horizons_hours=[6, 12, 24],
        )

        assert baseline_fc.status == ForecastStatus.SUCCESS
        baseline_speed = baseline_fc.translational_motion.speed_kmh
        baseline_bearing = baseline_fc.translational_motion.bearing_deg
        baseline_points = [
            (
                hp.lead_time_hours,
                hp.predicted_latitude,
                hp.predicted_longitude,
                hp.predicted_wind_persistence_knots,
                hp.predicted_wind_trend_knots,
            )
            for hp in baseline_fc.forecast_horizons
        ]

    # Step 2: In a transactional session, inject future observations with extreme coordinates
    with get_db_session(engine) as session:
        storm, _ = resolve_storm_in_database(session, storm_sid)
        # Find any valid source_asset_id
        asset = session.execute(select(SourceAsset)).scalars().first()

        # Add poison future records at T+1h, T+3h, T+6h, T+12h, T+24h
        future_times = [
            issue_time + timedelta(hours=1),
            issue_time + timedelta(hours=3),
            issue_time + timedelta(hours=6),
            issue_time + timedelta(hours=12),
            issue_time + timedelta(hours=24),
        ]

        poison_records = []
        for i, ft in enumerate(future_times):
            poison_lat = 45.0 + i
            poison_lon = 90.0 + i
            poison_obs = TrackObservation(
                id=uuid.uuid4(),
                storm_id=storm.id,
                source_asset_id=asset.id,
                source_agency="IMD",
                source_record_id=f"POISON_FUTURE_TEST_{i}",
                observation_time_utc=ft,
                latitude=poison_lat,  # Completely wild coordinates
                longitude=poison_lon,
                geom=WKTElement(f"POINT({poison_lon} {poison_lat})", srid=4326),
                wind_speed_knots=250.0,
                averaging_period="3-min",
                imd_category="SuCS",
            )
            session.add(poison_obs)
            poison_records.append(poison_obs)
        session.flush()

        # Step 3: Re-run forecast at the exact same issue time
        post_poison_fc = generate_forecast_from_db(
            session=session,
            storm_identifier=storm_sid,
            agency="IMD",
            issue_time_utc=issue_time,
            horizons_hours=[6, 12, 24],
        )

        # Assert identical results despite presence of future observations in DB
        assert post_poison_fc.status == ForecastStatus.SUCCESS
        assert post_poison_fc.translational_motion.speed_kmh == baseline_speed
        assert post_poison_fc.translational_motion.bearing_deg == baseline_bearing

        post_poison_points = [
            (
                hp.lead_time_hours,
                hp.predicted_latitude,
                hp.predicted_longitude,
                hp.predicted_wind_persistence_knots,
                hp.predicted_wind_trend_knots,
            )
            for hp in post_poison_fc.forecast_horizons
        ]

        assert post_poison_points == baseline_points

        # Roll back transaction to leave database completely clean
        session.rollback()


def test_database_read_only_behavior():
    """Verify forecast generation and hindsight verification perform zero database mutations."""
    engine = get_default_engine()
    issue_time = datetime(2023, 6, 11, 6, 0, tzinfo=UTC)

    with get_db_session(engine) as session:
        storms_before = session.query(func.count(Storm.id)).scalar()
        obs_before = session.query(func.count(TrackObservation.id)).scalar()
        aliases_before = session.query(func.count(StormAlias.id)).scalar()

        fc = generate_forecast_from_db(
            session=session,
            storm_identifier="2023156N10067",
            agency="IMD",
            issue_time_utc=issue_time,
        )
        assert fc.status == ForecastStatus.SUCCESS

        ver = verify_forecast_from_db(session, fc, tolerance_hours=3.0)
        assert ver.horizons_matched > 0

        storms_after = session.query(func.count(Storm.id)).scalar()
        obs_after = session.query(func.count(TrackObservation.id)).scalar()
        aliases_after = session.query(func.count(StormAlias.id)).scalar()

        assert storms_before == storms_after
        assert obs_before == obs_after
        assert aliases_before == aliases_after


def test_source_agency_consistency():
    """Verify that requesting IMD track does not mix JTWC or IBTrACS observations."""
    issue_time = datetime(2023, 6, 11, 6, 0, tzinfo=UTC)

    with get_db_session() as session:
        # Forecast with IMD
        fc_imd = generate_forecast_from_db(
            session=session,
            storm_identifier="BIPARJOY",
            agency="IMD",
            issue_time_utc=issue_time,
        )
        assert fc_imd.source_agency == "IMD"
        assert fc_imd.wind_averaging_period == "3-min"
        for p in fc_imd.historical_track_used:
            assert p.averaging_period == "3-min"

        # Forecast with JTWC
        fc_jtwc = generate_forecast_from_db(
            session=session,
            storm_identifier="BIPARJOY",
            agency="JTWC",
            issue_time_utc=issue_time,
        )
        assert fc_jtwc.source_agency == "JTWC"
        assert fc_jtwc.wind_averaging_period == "1-min"
        for p in fc_jtwc.historical_track_used:
            assert p.averaging_period in ["1-min", "unknown"]


def test_visual_demo_case_1_biparjoy_arabian_sea():
    """Verify visual demonstration case 1: Cyclone BIPARJOY in the Arabian Sea."""
    issue_t = datetime(2023, 6, 11, 6, 0, tzinfo=UTC)

    with get_db_session() as session:
        fc = generate_forecast_from_db(
            session=session,
            storm_identifier="2023156N10067",
            agency="IMD",
            issue_time_utc=issue_t,
            horizons_hours=[6, 12, 24],
        )

        assert fc.status == ForecastStatus.SUCCESS
        assert fc.storm_name == "BIPARJOY"
        assert fc.primary_basin == "NI"
        assert fc.input_observation_count >= 40
        assert fc.translational_motion.speed_kmh > 0.0

        # Verification
        ver = verify_forecast_from_db(session, fc, tolerance_hours=3.0)
        assert ver.horizons_matched == 3
        assert ver.mean_track_error_km is not None
        assert ver.mean_track_error_km < 60.0  # Operational benchmark


def test_visual_demo_case_2_amphan_bay_of_bengal():
    """Verify visual demonstration case 2: Super Cyclone AMPHAN in the Bay of Bengal."""
    issue_t = datetime(2020, 5, 18, 0, 0, tzinfo=UTC)

    with get_db_session() as session:
        fc = generate_forecast_from_db(
            session=session,
            storm_identifier="2020136N10088",
            agency="IMD",
            issue_time_utc=issue_t,
            horizons_hours=[6, 12, 24],
        )

        assert fc.status == ForecastStatus.SUCCESS
        assert fc.storm_name == "AMPHAN"
        assert fc.primary_basin == "NI"
        assert fc.input_observation_count >= 15
        assert fc.translational_motion.speed_kmh > 0.0

        # Verification
        ver = verify_forecast_from_db(session, fc, tolerance_hours=3.0)
        assert ver.horizons_matched == 3
        assert ver.mean_track_error_km is not None
        assert ver.mean_track_error_km < 85.0  # Operational benchmark


def test_visual_demo_case_3_remal_bay_of_bengal():
    """Verify visual demonstration case 3: Cyclone REMAL in northern Bay of Bengal."""
    issue_t = datetime(2024, 5, 25, 12, 0, tzinfo=UTC)

    with get_db_session() as session:
        fc = generate_forecast_from_db(
            session=session,
            storm_identifier="2024145N14087",
            agency="IMD",
            issue_time_utc=issue_t,
            horizons_hours=[6, 12, 24],
        )

        assert fc.status == ForecastStatus.SUCCESS
        assert fc.storm_name == "REMAL"
        assert fc.input_observation_count >= 10
        assert fc.translational_motion.speed_kmh > 0.0

        # Verification
        ver = verify_forecast_from_db(session, fc, tolerance_hours=3.0)
        assert ver.horizons_matched == 3
        assert ver.mean_track_error_km is not None
        assert ver.mean_track_error_km < 50.0  # Tight synoptic tracking


def test_api_endpoints_and_serialization(api_client):
    """Verify complete FastAPI operational workflow and GeoJSON serialization."""
    # 1. Health
    res_health = api_client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "OPERATIONAL"

    # 2. Demo cases
    res_cases = api_client.get("/api/forecast/demo-cases")
    assert res_cases.status_code == 200
    cases = res_cases.json()
    assert len(cases) >= 3
    case_sids = [c["storm_sid"] for c in cases]
    assert "2023156N10067" in case_sids
    assert "2020136N10088" in case_sids
    assert "2024145N14087" in case_sids

    # 3. Storms list
    res_storms = api_client.get("/api/storms?limit=10")
    assert res_storms.status_code == 200
    assert len(res_storms.json()) >= 1

    # 4. Storm detail
    res_storm = api_client.get("/api/storms/2023156N10067")
    assert res_storm.status_code == 200
    assert res_storm.json()["canonical_name"] == "BIPARJOY"

    # 5. Agency track
    res_track = api_client.get("/api/storms/2023156N10067/track?agency=IMD")
    assert res_track.status_code == 200
    track_data = res_track.json()
    assert track_data["source_agency"] == "IMD"
    assert track_data["observation_count"] >= 100
    assert track_data["geojson"]["type"] == "FeatureCollection"

    # 6. Generate forecast
    fc_req = {
        "storm_sid": "2023156N10067",
        "agency": "IMD",
        "issue_time_utc": "2023-06-11T06:00:00Z",
        "horizons_hours": [6, 12, 24],
    }
    res_fc = api_client.post("/api/forecast/generate", json=fc_req)
    assert res_fc.status_code == 200
    fc_data = res_fc.json()
    assert fc_data["status"] == "SUCCESS"
    assert len(fc_data["forecast_horizons"]) == 3
    assert fc_data["geojson"]["type"] == "FeatureCollection"

    # GeoJSON coordinate ordering check: [lon, lat]
    for feat in fc_data["geojson"]["features"]:
        if feat["geometry"]["type"] == "Point":
            coords = feat["geometry"]["coordinates"]
            assert len(coords) == 2
            lon, lat = coords
            assert 60.0 <= lon <= 80.0
            assert 10.0 <= lat <= 30.0

    # 7. Hindsight verification
    ver_req = {
        "forecast": fc_data,
        "tolerance_hours": 3.0,
    }
    res_ver = api_client.post("/api/forecast/verify", json=ver_req)
    assert res_ver.status_code == 200
    ver_data = res_ver.json()
    assert ver_data["horizons_matched"] == 3
    assert ver_data["mean_track_error_km"] is not None

    # 8. Methodology
    res_meth = api_client.get("/api/forecast/methodology")
    assert res_meth.status_code == 200
    assert (
        "rule" in res_meth.json()["core_subsystems"]["module_b"]["ground_truth_leakage_protection"]
    )
