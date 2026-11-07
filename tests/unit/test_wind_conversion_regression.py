"""Regression test suite for wind conversion removal and dataset evidence integrity.

Ensures:
1. Universal scalar wind conversion factors (such as WMO 0.88) are strictly eliminated.
2. CNN outputs remain purely in native 1-minute sustained wind speed (knots).
3. Deployed CNN inference resolution is verified at 128x128 pixels.
4. ConvLSTM spatiotemporal sequence endpoint reports actual elapsed time rather than fixed 3h.
5. Model registry metadata reports Band 13 (10.3 µm) and authentic checkpoint SHA-256 hashes.
"""

from fastapi.testclient import TestClient

from vayumarg.api.server import app
from vayumarg.ml.registry import TRUSTED_CHECKSUMS, get_model_registry
from vayumarg.ml.vision.inference import SatelliteInferenceEngine


def test_no_wmo_088_conversion_in_cnn_api():
    """Verify that the CNN inference API does not apply or return any 0.88 scalar conversion."""
    client = TestClient(app)
    response = client.post(
        "/api/ml/infer/satellite_cnn",
        json={"storm_name": "BIPARJOY", "channel": "TIR-1"},
    )
    assert response.status_code == 200, f"Unexpected error: {response.text}"
    data = response.json()

    assert data["status"] == "VERIFIED_EXPERIMENTAL"
    assert "predicted_1min_wind_knots" in data
    # Ensure forbidden fields from prior regression are absent
    assert "approx_3min_wind_knots_wmo_converted" not in data
    assert "wmo_converted_3min_wind_knots" not in data
    assert "conversion_disclaimer" not in data

    # Verify native convention documentation
    assert "1-minute" in data["native_label_convention"]
    assert "No universal scalar conversion factor exists" in data["averaging_period_note"]


def test_cnn_transform_resolution_is_128():
    """Verify that the deployed inference engine resizes satellite images to 128x128 px."""
    engine = SatelliteInferenceEngine()
    resize_transform = None
    for t in engine.cnn_transform.transforms:
        if hasattr(t, "size"):
            resize_transform = t
            break

    assert resize_transform is not None, "Resize transform not found in cnn_transform pipeline"
    assert resize_transform.size == (128, 128), (
        f"Expected (128, 128) resize resolution, got {resize_transform.size}"
    )


def test_convlstm_returns_dynamic_elapsed_time():
    """Verify that ConvLSTM reports actual elapsed hours from sequence timestamps."""
    client = TestClient(app)
    response = client.post(
        "/api/ml/infer/convlstm",
        json={"lead_time_hours": 3.0},
    )
    assert response.status_code == 200, f"Unexpected error: {response.text}"
    data = response.json()

    assert data["status"] == "VERIFIED_EXPERIMENTAL"
    assert "actual_elapsed_seconds" in data
    assert "actual_elapsed_hours" in data
    assert data["actual_elapsed_seconds"] > 0
    assert data["actual_elapsed_hours"] > 0
    assert "sequence_cadence_note" in data
    assert "irregular" in data["sequence_cadence_note"].lower()


def test_model_registry_metadata_and_checksum_integrity():
    """Verify registry attributions, 128x128 resolution, and authentic checkpoint hashes."""
    reg = get_model_registry()
    models = reg["models"]

    # Satellite CNN checks
    cnn = models["satellite_cnn"]
    assert cnn["checksum_verified"] is True
    assert cnn["status"] == "VERIFIED_EXPERIMENTAL"
    assert cnn["actual_sha256"] == TRUSTED_CHECKSUMS["satellite_cnn"]
    assert "Band 13" in cnn["training_data_source"]
    assert "10.3" in cnn["training_data_source"]
    assert "128×128" in cnn["input_modality"]

    # ConvLSTM checks
    conv = models["convlstm"]
    assert conv["checksum_verified"] is True
    assert conv["status"] == "VERIFIED_EXPERIMENTAL"
    assert conv["actual_sha256"] == TRUSTED_CHECKSUMS["convlstm"]

    # Track GRU checks
    gru = models["track_gru"]
    assert gru["checksum_verified"] is True
    assert gru["status"] == "VERIFIED_EXPERIMENTAL"
    assert gru["actual_sha256"] == TRUSTED_CHECKSUMS["track_gru"]
