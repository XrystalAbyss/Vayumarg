"""Unit tests for Vayumarg AI Model Lab registry and inference services."""

import pytest
from fastapi.testclient import TestClient

from vayumarg.api.server import app
from vayumarg.ml.registry import MLInferenceState, get_model_registry
from vayumarg.ml.track.inference import TrackInferenceEngine


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_registry_cryptographic_verification():
    """Verify that all three models exist and have valid cryptographic SHA-256 digests."""
    reg = get_model_registry()
    assert reg["status"] == "OPERATIONAL"
    models = reg["models"]

    # 1. Satellite CNN
    assert "satellite_cnn" in models
    assert models["satellite_cnn"]["status"] == MLInferenceState.VERIFIED_EXPERIMENTAL.value
    assert models["satellite_cnn"]["checksum_verified"] is True

    # 2. ConvLSTM
    assert "convlstm" in models
    assert models["convlstm"]["status"] == MLInferenceState.VERIFIED_EXPERIMENTAL.value
    assert models["convlstm"]["checksum_verified"] is True

    # 3. Track GRU
    assert "track_gru" in models
    assert models["track_gru"]["status"] == MLInferenceState.VERIFIED_EXPERIMENTAL.value
    assert models["track_gru"]["checksum_verified"] is True


def test_track_inference_engine():
    """Verify TrackInferenceEngine loads and generates valid multi-horizon predictions."""
    engine = TrackInferenceEngine()
    assert engine.is_ready() is True
    assert engine.sha256 is not None

    sample_fixes = [
        {"lat": 15.0 + i * 0.2, "lon": 68.0 + i * 0.1, "wind_kt": 60.0 + i * 2}
        for i in range(8)
    ]
    res = engine.predict(sample_fixes)
    assert res["model_id"] == "vayumarg-track-gru-v1"
    assert len(res["forecasts"]) == 3

    for fc in res["forecasts"]:
        assert fc["horizon_h"] in [6, 12, 24]
        assert "gru_predicted" in fc
        assert "geodesic_baseline" in fc
        assert 0.0 < fc["gru_predicted"]["latitude"] < 40.0
        assert 50.0 < fc["gru_predicted"]["longitude"] < 100.0


def test_api_ml_registry_endpoint(client: TestClient):
    """Test GET /api/ml/registry returns 200 and all verified models."""
    resp = client.get("/api/ml/registry")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert "models" in data
    assert data["models"]["track_gru"]["status"] == "VERIFIED_EXPERIMENTAL"


def test_api_infer_track_gru_endpoint(client: TestClient):
    """Test POST /api/ml/infer/track_gru returns real predictions for BIPARJOY."""
    resp = client.post("/api/ml/infer/track_gru", json={"storm_name": "BIPARJOY"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "VERIFIED_EXPERIMENTAL"
    assert data["storm_name"] == "BIPARJOY"
    forecasts = data["forecast_result"]["forecasts"]
    assert len(forecasts) == 3
    assert forecasts[0]["horizon_h"] == 6
    assert forecasts[1]["horizon_h"] == 12
    assert forecasts[2]["horizon_h"] == 24
    assert "gru_predicted" in forecasts[0]
    assert "geodesic_baseline" in forecasts[0]
    assert "hybrid_predicted" in forecasts[0]


def test_api_track_storms_endpoint(client: TestClient):
    """Test GET /api/ml/track/storms returns available storms."""
    resp = client.get("/api/ml/track/storms")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_available"] >= 4
    names = [s["name"] for s in data["storms"]]
    assert "BIPARJOY" in names


def test_satellite_cnn_no_scalar_conversion_and_taxonomy(client: TestClient):
    """Test POST /api/ml/infer/satellite_cnn strictly does not perform universal 0.88 scalar conversion

    and exposes source-native 1-minute sustained wind, dual-head taxonomy, and averaging period notes.
    """
    resp = client.post(
        "/api/ml/infer/satellite_cnn",
        json={"storm_name": "BIPARJOY", "channel": "TIR-1"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # P0 Scientific Integrity Assertions:
    # 1. No universal 0.88 scalar conversion field
    assert "approx_3min_wind_knots_wmo_converted" not in data, (
        "Forbidden universal scalar wind conversion field detected in response!"
    )

    # 2. Source-native 1-minute wind prediction present
    assert "predicted_1min_wind_knots" in data
    assert isinstance(data["predicted_1min_wind_knots"], (int, float))
    assert data["predicted_1min_wind_knots"] > 0

    # 3. Explicit averaging period note
    assert "averaging_period_note" in data
    assert "1-minute" in data["averaging_period_note"]
    assert "3-minute" in data["averaging_period_note"]

    # 4. Dual-head classification & agreement
    assert "classifier_predicted_bin" in data
    assert "predicted_category_label" in data
    assert "regression_implied_bin" in data
    assert "heads_in_agreement" in data
    assert isinstance(data["heads_in_agreement"], bool)


def test_convlstm_inference_endpoint(client: TestClient):
    """Test POST /api/ml/infer/convlstm returns sequence inference with reconstructed frame."""
    seq_resp = client.get("/api/ml/convlstm/sequences")
    assert seq_resp.status_code == 200
    seqs = seq_resp.json().get("sequences", [])
    assert len(seqs) > 0

    first_seq = seqs[0]["sequence_id"]
    resp = client.post("/api/ml/infer/convlstm", json={"sequence_id": first_seq})
    assert resp.status_code == 200
    data = resp.json()

    assert data["sequence_id"] == first_seq
    assert "predicted_future_wind_kt" in data
    assert "persistence_baseline_error_kt" in data
    assert "reconstructed_next_frame_b64" in data
    assert len(data["input_frames"]) == 3


def test_registry_scientific_lineage_and_ci():
    """Verify registry includes computed ConvLSTM persistence MSE and Track GRU bootstrap CI."""
    reg = get_model_registry()
    models = reg["models"]

    # ConvLSTM Image Persistence vs Wind Persistence
    conv_metrics = models["convlstm"]["benchmark_metrics"]
    assert conv_metrics["next_frame_pixel_mse"] == 0.01084
    assert conv_metrics["last_frame_persistence_pixel_mse"] == 0.01328
    assert conv_metrics["image_reconstruction_skill_pct"] == 18.35

    # Track GRU Bootstrap CI & Baseline Superiority
    track_comparison = models["track_gru"]["baseline_comparison"]
    assert "geodesic_superiority_note" in track_comparison
    assert track_comparison["geodesic_track_error_km"]["+24h"] == 180.5
    assert track_comparison["gru_track_error_km"]["+24h"] == 239.3
    assert track_comparison["geodesic_track_error_km"]["+24h"] < track_comparison["gru_track_error_km"]["+24h"]

    wind_24h = track_comparison["wind_persistence_at_24h"]
    assert "[-0.863 kt, +0.786 kt]" in wind_24h["bootstrap_95ci_kt"]
    assert "inconclusive" in wind_24h["statistical_conclusion"].lower()

