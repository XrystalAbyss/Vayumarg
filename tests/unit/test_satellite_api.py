"""Unit tests for FastAPI satellite intelligence API routes."""

import pytest
from starlette.testclient import TestClient

from vayumarg.api.app import app
from vayumarg.satellite.provenance import DANA_IMD_INELIGIBILITY_NOTICE


@pytest.fixture(scope="module")
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


def test_root_and_health(client: TestClient):
    """Verify root and health endpoints."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "OPERATIONAL"
    assert res.json()["module_a"] == "AUTHENTIC_SATELLITE_INTELLIGENCE_READY"

    res_health = client.get("/api/v1/satellite/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "HEALTHY"
    assert data["verified_crops_count"] >= 4
    assert "REMAL" in data["authentic_storms"]
    assert "DANA" in data["authentic_storms"]


def test_list_crops_endpoint(client: TestClient):
    """Verify listing all authentic satellite crops."""
    res = client.get("/api/v1/satellite/crops")
    assert res.status_code == 200
    crops = res.json()
    assert len(crops) >= 4
    storms = [c["storm_name"] for c in crops]
    assert {"REMAL", "DANA", "AMPHAN", "BIPARJOY"}.issubset(set(storms))

    # Check DANA notice in listing
    dana = [c for c in crops if c["storm_name"] == "DANA"][0]
    assert dana["primary_imd_eligible"] is False
    assert dana["dana_ineligibility_notice"] == DANA_IMD_INELIGIBILITY_NOTICE


def test_get_crop_metadata_and_provenance(client: TestClient):
    """Verify full metadata retrieval for an authentic crop."""
    res = client.get("/api/v1/satellite/crops/REMAL")
    assert res.status_code == 200
    data = res.json()
    assert data["storm_name"] == "REMAL"
    assert data["satellite"] == "INSAT-3DR"
    assert data["verification_status"] == "REAL_VERIFIED"
    assert (
        data["source_sha256"] == "5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807"
    )
    assert data["crop_sha256"] == "7649f8f0711dd88a146b33ec96b000bdf9819e65a5fe3552294f96b27faebd90"


def test_get_current_state_labels(client: TestClient):
    """Verify current-state labels for REMAL (eligible) and DANA (ineligible policy)."""
    # REMAL
    res_r = client.get("/api/v1/satellite/crops/REMAL/labels")
    assert res_r.status_code == 200
    data_r = res_r.json()
    assert data_r["primary_imd_eligible"] is True
    assert data_r["primary_imd_observation"]["cyclone_category"] == "SCS"
    assert data_r["primary_imd_observation"]["wind_speed_knots"] == 60.0

    # DANA
    res_d = client.get("/api/v1/satellite/crops/DANA/labels")
    assert res_d.status_code == 200
    data_d = res_d.json()
    assert data_d["primary_imd_eligible"] is False
    assert data_d["dana_ineligibility_notice"] == DANA_IMD_INELIGIBILITY_NOTICE
    assert data_d["primary_imd_observation"] is None
    assert data_d["secondary_jtwc_observation"] is not None


def test_get_channel_analytics(client: TestClient):
    """Verify channel quantitative analytics endpoint."""
    res = client.get("/api/v1/satellite/crops/BIPARJOY/channels/TIR-1")
    assert res.status_code == 200
    data = res.json()
    assert data["channel_name"] == "TIR-1"
    assert data["total_pixels"] == 40401
    assert data["valid_fraction"] > 0.99
    assert data["min_tb_k"] is not None
    assert "p50" in data["percentiles_tb_k"]
    assert len(data["cold_cloud_fractions"]) == 4
    assert len(data["radial_profile"]) == 7
    assert data["gradient_statistics"]["mean_k_per_km"] > 0.0


def test_channel_switching_and_preview_endpoint(client: TestClient):
    """Verify preview images for TIR-1, WV, TIR-2, MIR and channel switching."""
    for ch in ["TIR-1", "WV", "TIR-2", "MIR"]:
        res = client.get(
            f"/api/v1/satellite/crops/AMPHAN/channels/{ch}/preview?colormap=thermal_ir"
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        assert res.headers["x-scientific-source"] == "REAL_VERIFIED_INSAT"
        assert len(res.content) > 500


def test_colormap_legends_endpoints(client: TestClient):
    """Verify colormap legend metadata and image endpoints."""
    res_meta = client.get("/api/v1/satellite/legends/thermal_ir")
    assert res_meta.status_code == 200
    data = res_meta.json()
    assert data["temp_min_k"] == 180.0
    assert data["temp_max_k"] == 310.0
    assert len(data["ticks"]) >= 5

    res_img = client.get("/api/v1/satellite/legends/thermal_ir/image")
    assert res_img.status_code == 200
    assert res_img.headers["content-type"] == "image/png"
    assert len(res_img.content) > 500


def test_error_handling(client: TestClient):
    """Verify 404 for unknown storm and 400 for invalid channel."""
    res_unknown = client.get("/api/v1/satellite/crops/NONEXISTENT_STORM")
    assert res_unknown.status_code == 404

    res_invalid_ch = client.get("/api/v1/satellite/crops/REMAL/channels/INVALID_CHANNEL/preview")
    assert res_invalid_ch.status_code == 400
