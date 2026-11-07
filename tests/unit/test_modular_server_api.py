"""Unit tests for the refactored modular FastAPI server endpoints."""

from fastapi.testclient import TestClient

from vayumarg.api.server import app

client = TestClient(app)


def test_server_health_and_summary():
    """Verify operational health and summary endpoints."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "database_backend" in data

    res_sum = client.get("/api/summary")
    assert res_sum.status_code == 200
    assert res_sum.json()["mode"] in ["DATABASE_POSTGRES", "OFFLINE_DEMO_CACHE"]


def test_server_storms_catalog_and_alias():
    """Verify storm listing and dual canonical_sid / storm_sid presence."""
    res = client.get("/api/storms?limit=5")
    assert res.status_code == 200
    storms = res.json()
    assert len(storms) >= 1
    for s in storms:
        assert "canonical_sid" in s
        assert "storm_sid" in s
        assert s["canonical_sid"] == s["storm_sid"]


def test_server_storm_detail_and_track():
    """Verify storm profile and track retrieval."""
    res = client.get("/api/storms/BIPARJOY")
    assert res.status_code == 200
    profile = res.json()
    assert profile["canonical_name"] == "BIPARJOY"
    assert profile["canonical_sid"] == "2023156N10067"
    assert profile["storm_sid"] == "2023156N10067"

    res_track = client.get("/api/storms/BIPARJOY/track?agency=IMD")
    assert res_track.status_code == 200
    track = res_track.json()
    assert track["source_agency"] == "IMD"
    assert "geojson" in track


def test_server_forecast_generation_with_dual_sids():
    """Verify forecast generation works with both storm_sid and canonical_sid."""
    # Test with storm_sid
    payload1 = {
        "storm_sid": "2023156N10067",
        "issue_time_utc": "2023-06-11T06:00:00Z",
        "agency": "IMD",
        "horizons_hours": [6, 12, 24],
    }
    res1 = client.post("/api/forecast/generate", json=payload1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "forecast_points" in data1
    assert len(data1["forecast_points"]) == 3

    # Test with canonical_sid
    payload2 = {
        "canonical_sid": "2023156N10067",
        "issue_time_utc": "2023-06-11T06:00:00Z",
        "agency": "IMD",
        "horizons_hours": [6, 12, 24],
    }
    res2 = client.post("/api/forecast/generate", json=payload2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["forecast_points"]) == 3


def test_server_satellite_crops_and_metrics():
    """Verify satellite crop listing and physical metric extraction."""
    res = client.get("/api/satellite/crops")
    assert res.status_code == 200
    crops = res.json()
    assert len(crops) >= 1

    res_metrics = client.get("/api/satellite/crop/BIPARJOY/metrics?channel=TIR-1")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert metrics["storm_name"] == "BIPARJOY"
    assert "temperature_quantiles_kelvin" in metrics

