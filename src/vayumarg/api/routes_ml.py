"""FastAPI Router for Vayumarg AI Model Lab and Scientific Inference Services.

Exposes endpoints for:
- Authoritative read-only ML model registry with cryptographic checksum verification.
- Scientific inference delegation with explicit operational states:
  VERIFIED_EXPERIMENTAL, UNVERIFIED_DATA, MODEL_UNAVAILABLE, INPUT_INCOMPATIBLE, INFERENCE_ERROR.
- Single-frame satellite infrared intensity regression (ResNet-18).
- Spatiotemporal satellite sequence forecasting and next-frame reconstruction (ConvLSTM).
- Recurrent track trajectory forecasting (GRU/LSTM) status and operational baseline delegation.
- Pre-computed cross-domain evaluations on authentic ISRO INSAT-3DR/3DS crops.
"""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from vayumarg.ml.registry import (
    TRUSTED_CHECKSUMS,
    MLInferenceState,
    compute_file_sha256,
    get_model_registry,
)
from vayumarg.ml.track.inference import TrackInferenceEngine
from vayumarg.ml.vision.inference import SatelliteInferenceEngine

logger = logging.getLogger("vayumarg.api.ml")

router = APIRouter(prefix="/api/ml", tags=["AI Model Lab"])

# Project root paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "satellite" / "nasa_cyclone" / "images"
SEQUENCES_FILE = (
    PROJECT_ROOT / "data" / "processed" / "satellite" / "nasa_cyclone" / "sequences_manifest.json"
)
MODELS_DIR = PROJECT_ROOT / "models" / "vayumarg" / "vision"
TRACK_MODELS_DIR = PROJECT_ROOT / "models" / "vayumarg"
DEMO_STORMS_DIR = PROJECT_ROOT / "data" / "demo_cache" / "storms"

# Lazy-loaded singleton inference engines
_inference_engine: SatelliteInferenceEngine | None = None
_track_engine: TrackInferenceEngine | None = None


def get_engine() -> SatelliteInferenceEngine:
    """Lazy-load the satellite inference engine on first request."""
    global _inference_engine
    if _inference_engine is None:
        logger.info("Lazy-loading SatelliteInferenceEngine...")
        _inference_engine = SatelliteInferenceEngine()
    return _inference_engine


def get_track_engine() -> TrackInferenceEngine:
    """Lazy-load the track inference engine on first request."""
    global _track_engine
    if _track_engine is None:
        logger.info("Lazy-loading TrackInferenceEngine...")
        _track_engine = TrackInferenceEngine()
    return _track_engine


# Request Schemas
class CNNInferenceRequest(BaseModel):
    storm_name: str = Field(
        ..., description="Storm name for authentic crop (e.g. BIPARJOY, AMPHAN, REMAL, DANA)"
    )
    channel: str = Field("TIR-1", description="Infrared channel (e.g. TIR-1, TIR-2)")


class ConvLSTMInferenceRequest(BaseModel):
    sequence_id: str | None = Field(
        None, description="Sequence identifier from sequences_manifest.json"
    )
    lead_time_hours: float = Field(3.0, description="Forecast lead time in hours")


class TrackGRUInferenceRequest(BaseModel):
    storm_name: str = Field(..., description="Target cyclone canonical name")
    issue_time: str | None = Field(None, description="Forecast issuance timestamp")


# --------------------------------------------------------------------------
# Registry Endpoints
# --------------------------------------------------------------------------


@router.get("/registry", summary="Retrieve Authoritative AI/ML Model Registry")
def get_registry() -> dict[str, Any]:
    """Retrieve the authoritative read-only registry of all AI/ML models in Vayumarg.

    Verifies checkpoint presence, validates SHA-256 checksums against trusted
    forensic records, and reports training/evaluation metadata.
    """
    try:
        return get_model_registry()
    except Exception as e:
        logger.error("Error retrieving model registry: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to load model registry: {str(e)}") from e


@router.get("/models/{model_id}", summary="Get Specific Model Registry Record")
def get_model_detail(model_id: str) -> dict[str, Any]:
    """Retrieve detailed registry specifications, benchmark metrics, and limitations for a model."""
    registry = get_model_registry()
    models = registry.get("models", {})
    if model_id not in models:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry. Available: {list(models.keys())}",
        )
    return {
        "model": models[model_id],
        "hardware": registry.get("hardware"),
    }


# --------------------------------------------------------------------------
# Scientific Inference Endpoints
# --------------------------------------------------------------------------


@router.post("/infer/satellite_cnn", summary="Execute ResNet-18 Satellite Intensity Inference")
def infer_satellite_cnn(req: CNNInferenceRequest) -> dict[str, Any]:
    """Run single-frame infrared intensity regression on authentic ISRO INSAT crop.

    Enforces forensic release gate: validates model checksum before invocation.
    Returns explicit state: VERIFIED_EXPERIMENTAL, UNVERIFIED_DATA, or INFERENCE_ERROR.
    """
    # 1. Forensic Checksum Release Gate
    cnn_ckpt = MODELS_DIR / "satellite_cnn_best.pt"
    if not cnn_ckpt.exists():
        return {
            "status": MLInferenceState.MODEL_UNAVAILABLE.value,
            "message": "Satellite CNN checkpoint 'satellite_cnn_best.pt' is missing from disk.",
            "prediction": None,
        }

    actual_hash = compute_file_sha256(cnn_ckpt)
    if actual_hash != TRUSTED_CHECKSUMS["satellite_cnn"]:
        return {
            "status": MLInferenceState.UNVERIFIED_DATA.value,
            "message": "Forensic checksum verification failed. Model weights do not match trusted SHA-256.",
            "expected_sha256": TRUSTED_CHECKSUMS["satellite_cnn"],
            "actual_sha256": actual_hash,
            "prediction": None,
        }

    # 2. Execute Inference
    try:
        engine = get_engine()
        pred = engine.evaluate_insat_crop(req.storm_name, channel=req.channel)

        raw_1min_kt = pred["predicted_max_sustained_wind_knots"]

        # Source-native 1-minute wind bins (thresholds: 28, 34, 48, 64, 90 kt)
        bin_names = [
            "Bin 0 (<28 kt)",
            "Bin 1 (28-33 kt)",
            "Bin 2 (34-47 kt)",
            "Bin 3 (48-63 kt)",
            "Bin 4 (64-89 kt)",
            "Bin 5 (>=90 kt)",
        ]

        def get_source_wind_bin(w: float) -> tuple[int, str]:
            if w < 28.0:
                return 0, bin_names[0]
            elif w < 34.0:
                return 1, bin_names[1]
            elif w < 48.0:
                return 2, bin_names[2]
            elif w < 64.0:
                return 3, bin_names[3]
            elif w < 90.0:
                return 4, bin_names[4]
            else:
                return 5, bin_names[5]

        reg_bin_idx, reg_bin_name = get_source_wind_bin(raw_1min_kt)
        cls_bin_idx = pred.get("predicted_category_index", reg_bin_idx)
        cls_bin_name = bin_names[cls_bin_idx] if 0 <= cls_bin_idx < len(bin_names) else f"Bin {cls_bin_idx}"

        heads_agree = reg_bin_idx == cls_bin_idx
        disagreement_note = (
            None
            if heads_agree
            else (
                f"Dual-head discrepancy: Classifier head predicted {cls_bin_name}, "
                f"whereas regression head predicted {raw_1min_kt} kt which falls into {reg_bin_name}."
            )
        )

        return {
            "status": MLInferenceState.VERIFIED_EXPERIMENTAL.value,
            "model_id": "satellite_cnn",
            "model_name": "ResNet-18 Infrared Cyclone Intensity Regressor",
            "storm_name": req.storm_name.upper(),
            "channel": req.channel,
            "native_label_convention": "1-minute sustained wind in knots (NOAA / JTWC standard)",
            "predicted_1min_wind_knots": raw_1min_kt,
            "averaging_period_note": (
                "Model output is strictly 1-minute sustained wind in knots (NOAA / JTWC convention). "
                "No universal scalar conversion factor exists to convert 1-minute to IMD 3-minute sustained winds. "
                "Comparisons against IMD operational advisories represent non-equivalent, exploratory cross-domain evaluations."
            ),
            "classifier_predicted_bin": cls_bin_name,
            "regression_implied_bin": reg_bin_name,
            "heads_in_agreement": heads_agree,
            "head_disagreement_note": disagreement_note,
            "predicted_category_label": pred["predicted_category_label"],
            "category_probabilities": pred["category_probabilities"],
            "estimated_uncertainty_kt": pred["estimated_uncertainty_kt"],
            "inference_latency_ms": pred["inference_latency_ms"],
            "source_domain": pred["source_domain"],
            "scientific_limitations": pred["domain_transfer_disclaimer"],
        }
    except FileNotFoundError as fnf:
        return {
            "status": MLInferenceState.INPUT_INCOMPATIBLE.value,
            "message": str(fnf),
            "prediction": None,
        }
    except Exception as e:
        logger.error("Inference failed for %s: %s", req.storm_name, e)
        return {
            "status": MLInferenceState.INFERENCE_ERROR.value,
            "message": f"Inference execution error: {str(e)}",
            "prediction": None,
        }


@router.post("/infer/convlstm", summary="Execute ConvLSTM Spatiotemporal Sequence Forecast")
def infer_convlstm(req: ConvLSTMInferenceRequest) -> dict[str, Any]:
    """Run ConvLSTM spatiotemporal sequence prediction on chronological satellite frames.

    Returns 3 past input frames, predicted future intensity, and reconstructed next frame.
    Enforces forensic release gate before execution.
    """
    # 1. Forensic Checksum Release Gate
    conv_ckpt = MODELS_DIR / "satellite_convlstm_best.pt"
    if not conv_ckpt.exists():
        return {
            "status": MLInferenceState.MODEL_UNAVAILABLE.value,
            "message": "ConvLSTM checkpoint 'satellite_convlstm_best.pt' is missing from disk.",
            "forecast": None,
        }

    actual_hash = compute_file_sha256(conv_ckpt)
    if actual_hash != TRUSTED_CHECKSUMS["convlstm"]:
        return {
            "status": MLInferenceState.UNVERIFIED_DATA.value,
            "message": "Forensic checksum verification failed for ConvLSTM checkpoint.",
            "forecast": None,
        }

    # 2. Resolve Sequence from Manifest
    if not SEQUENCES_FILE.exists():
        return {
            "status": MLInferenceState.INPUT_INCOMPATIBLE.value,
            "message": "Sequences manifest not found.",
            "forecast": None,
        }

    try:
        data = json.loads(SEQUENCES_FILE.read_text(encoding="utf-8"))
        sequences = data.get("sequences", [])

        # Select requested sequence or default to a high-intensity held-out test sequence (dzw or xtd)
        selected_seq = None
        if req.sequence_id:
            for s in sequences:
                if s.get("sequence_id") == req.sequence_id:
                    selected_seq = s
                    break

        if selected_seq is None:
            # Pick first test sequence
            for s in sequences:
                if s.get("split") == "test":
                    selected_seq = s
                    break

        if not selected_seq:
            return {
                "status": MLInferenceState.INPUT_INCOMPATIBLE.value,
                "message": "No valid held-out test sequence found in manifest.",
                "forecast": None,
            }

        # 3. Load Authentic Frames
        from PIL import Image

        input_paths = selected_seq["input_frames"]
        frame_imgs = []
        frame_urls = []
        for p_str in input_paths:
            p = PROJECT_ROOT / p_str
            if not p.exists():
                raise FileNotFoundError(f"Sequence frame file missing: {p}")
            frame_imgs.append(Image.open(p))
            frame_urls.append(f"/api/ml/image/{p.name}")

        target_p = PROJECT_ROOT / selected_seq["target_frame"]
        target_url = f"/api/ml/image/{target_p.name}" if target_p.exists() else None

        # 4. Run Inference
        engine = get_engine()
        res = engine.predict_sequence(frame_imgs, lead_time_hours=req.lead_time_hours)

        # Baseline delta
        current_wind = selected_seq["past_winds"][-1]
        target_wind = selected_seq["target_wind"]
        pred_wind_val = res.get(
            "predicted_future_wind_knots", res.get("predicted_future_wind_kt", 0.0)
        )
        persistence_error = abs(current_wind - target_wind)
        pred_error = abs(pred_wind_val - target_wind)

        # Elapsed time from raw capture sequence metadata
        actual_elapsed_seconds = selected_seq.get("time_step_seconds", 10800)
        actual_elapsed_hours = round(actual_elapsed_seconds / 3600.0, 2)

        return {
            "status": MLInferenceState.VERIFIED_EXPERIMENTAL.value,
            "model_id": "convlstm",
            "sequence_id": selected_seq["sequence_id"],
            "storm_id": selected_seq["storm_id"],
            "split": selected_seq.get("split", "test"),
            "lead_time_hours": actual_elapsed_hours,
            "actual_elapsed_seconds": actual_elapsed_seconds,
            "actual_elapsed_hours": actual_elapsed_hours,
            "sequence_cadence_note": (
                f"Target frame is {actual_elapsed_hours}h ({actual_elapsed_seconds}s) after the latest input frame. "
                "Raw NASA competition capture cadence is irregular (mean ~3h, range 0.5h–40.5h); "
                "ConvLSTM evaluates sequential observation transitions rather than fixed uniform time steps."
            ),
            "input_frames": frame_urls,
            "target_frame_url": target_url,
            "past_observed_winds_kt": selected_seq["past_winds"],
            "ground_truth_target_wind_kt": target_wind,
            "predicted_future_wind_kt": pred_wind_val,
            "prediction_absolute_error_kt": round(pred_error, 1),
            "persistence_baseline_error_kt": round(persistence_error, 1),
            "reconstructed_next_frame_b64": res.get("reconstructed_next_frame_b64"),
            "inference_latency_ms": res.get("inference_latency_ms"),
            "scientific_limitations": [
                "Operates on 64×64 downsampled spatial resolution due to recurrent BPTT memory constraints.",
                "Persistence baseline (1.90 kt MAE) is mathematically dominant on short 1-3 hour temporal horizons.",
                "Observation intervals vary across sequences depending on satellite orbit and capture cadence.",
                "Primary utility is continuous cloud canopy and advective motion modeling (0.01084 pixel MSE).",
            ],
        }
    except Exception as e:
        logger.error("ConvLSTM inference failed: %s", e)
        return {
            "status": MLInferenceState.INFERENCE_ERROR.value,
            "message": f"ConvLSTM execution error: {str(e)}",
            "forecast": None,
        }


@router.post("/infer/track_gru", summary="Request Recurrent Track Forecast (Vayumarg-Track-GRU)")
def infer_track_gru(req: TrackGRUInferenceRequest) -> dict[str, Any]:
    """Request multi-horizon trajectory & intensity inference from Vayumarg-Track-GRU.

    Enforces forensic release gate: validates model checksum before invocation.
    Loads chronological track history for the requested cyclone from the verified archive,
    generates +6h, +12h, +24h forecasts, and benchmarks against Geodesic & Persistence baselines.
    """
    # 1. Forensic Checksum Release Gate
    track_ckpt = TRACK_MODELS_DIR / "track_gru_best.pt"
    if not track_ckpt.exists():
        return {
            "status": MLInferenceState.MODEL_UNAVAILABLE.value,
            "message": "Track GRU checkpoint 'track_gru_best.pt' is missing from disk.",
            "forecast": None,
        }

    actual_hash = compute_file_sha256(track_ckpt)
    expected_hash = TRUSTED_CHECKSUMS.get("track_gru")
    if actual_hash != expected_hash:
        return {
            "status": MLInferenceState.UNVERIFIED_DATA.value,
            "message": "Forensic checksum verification failed for Track GRU checkpoint.",
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "forecast": None,
        }

    # 2. Locate historical fixes for requested storm
    storm_clean = req.storm_name.upper().strip()
    track_file = DEMO_STORMS_DIR / f"{storm_clean}_track.json"

    if not track_file.exists():
        # Search for any file matching storm_clean
        candidates = list(DEMO_STORMS_DIR.glob(f"*{storm_clean}*_track.json"))
        if candidates:
            track_file = candidates[0]
        else:
            return {
                "status": MLInferenceState.INPUT_INCOMPATIBLE.value,
                "message": f"Historical track for storm '{storm_clean}' not found in verified archive.",
                "available_storms": [
                    "BIPARJOY",
                    "AMPHAN",
                    "REMAL",
                    "DANA",
                    "FANI",
                    "TAUKTAE",
                    "MOCHA",
                    "YAAS",
                ],
            }

    try:
        raw_track = json.loads(track_file.read_text(encoding="utf-8"))
        fixes = []
        for fix in raw_track:
            lat = fix.get("latitude")
            lon = fix.get("longitude")
            w = (
                fix.get("jtwc_wind_speed_knots")
                or fix.get("imd_wind_speed_knots")
                or fix.get("wind_speed_knots")
                or 35.0
            )
            if lat is not None and lon is not None:
                fixes.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "wind_kt": float(w),
                        "time": fix.get("iso_time") or fix.get("observation_time_utc", ""),
                    }
                )

        if len(fixes) < 10:
            return {
                "status": MLInferenceState.INPUT_INCOMPATIBLE.value,
                "message": f"Storm '{storm_clean}' has only {len(fixes)} fixes (minimum 10 required for evaluation).",
                "forecast": None,
            }

        # Choose observation point: if issue_time supplied find index, else pick ~60% through the track
        obs_idx = len(fixes) // 2
        if req.issue_time:
            for idx, fix in enumerate(fixes):
                if fix.get("time") and req.issue_time in fix["time"]:
                    obs_idx = idx
                    break

        # Ensure at least 8 fixes in history
        obs_idx = max(7, min(obs_idx, len(fixes) - 9))

        history = fixes[obs_idx - 7 : obs_idx + 1]
        # Ground truth targets: +6h (+2 fixes), +12h (+4 fixes), +24h (+8 fixes)
        ground_truth = []
        for offset in [2, 4, 8]:
            target_idx = obs_idx + offset
            if target_idx < len(fixes):
                ground_truth.append(fixes[target_idx])

        # 3. Execute Track GRU Inference
        engine = get_track_engine()
        result = engine.predict(
            history, future_fixes=ground_truth if len(ground_truth) == 3 else None
        )

        return {
            "status": MLInferenceState.VERIFIED_EXPERIMENTAL.value,
            "model_id": "track_gru",
            "storm_name": storm_clean,
            "issue_time": fixes[obs_idx].get("time"),
            "observation_index": obs_idx,
            "total_fixes": len(fixes),
            "forecast_result": result,
            "scientific_baseline_comparison": {
                "geodesic_extrapolation": "Constant-velocity Great-Circle forward projection",
                "persistence": "Stationary coordinate & constant-wind persistence",
                "notes": (
                    "In tropical cyclones, 6h-12h linear inertial motion is a mathematically strong baseline. "
                    "Vayumarg-Track-GRU incorporates temporal attention over 24h of history to capture curvature and intensity evolution."
                ),
            },
        }
    except Exception as e:
        logger.error("Track GRU inference failed: %s", e)
        return {
            "status": MLInferenceState.INFERENCE_ERROR.value,
            "message": f"Track GRU execution error: {str(e)}",
            "forecast": None,
        }


@router.get("/track/storms", summary="List Available Historical Storms for Track Forecasting")
def list_track_storms() -> dict[str, Any]:
    """List historical storms with verified track archives available for interactive Track GRU forecasting."""
    storms = []
    if DEMO_STORMS_DIR.exists():
        for f in sorted(DEMO_STORMS_DIR.glob("*_track.json")):
            name = f.stem.replace("_track", "")
            if not name.isdigit():  # Filter out SID-based filenames if named ones exist
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    storms.append(
                        {
                            "name": name,
                            "fixes_count": len(data),
                            "first_time": data[0].get("iso_time")
                            or data[0].get("observation_time_utc")
                            if data
                            else None,
                            "last_time": data[-1].get("iso_time")
                            or data[-1].get("observation_time_utc")
                            if data
                            else None,
                        }
                    )
                except Exception:
                    pass
    return {
        "total_available": len(storms),
        "storms": storms,
    }


# --------------------------------------------------------------------------
# Supporting Data & Asset Endpoints
# --------------------------------------------------------------------------


@router.get("/convlstm/sequences", summary="List Available Test Sequences for ConvLSTM")
def list_convlstm_sequences(split: str = "test") -> dict[str, Any]:
    """List chronological sequence records available for interactive ConvLSTM forecasting."""
    if not SEQUENCES_FILE.exists():
        return {"sequences": []}
    try:
        data = json.loads(SEQUENCES_FILE.read_text(encoding="utf-8"))
        seqs = [s for s in data.get("sequences", []) if s.get("split") == split]
        # Summarize for client
        summary = []
        for s in seqs[:20]:  # Return top 20 curated test sequences
            summary.append(
                {
                    "sequence_id": s["sequence_id"],
                    "storm_id": s["storm_id"],
                    "split": s["split"],
                    "past_winds": s["past_winds"],
                    "target_wind": s["target_wind"],
                    "frame_count": len(s["input_frames"]),
                }
            )
        return {
            "total_available": len(seqs),
            "sample_count": len(summary),
            "sequences": summary,
        }
    except Exception as e:
        logger.error("Could not read sequences manifest: %s", e)
        return {"sequences": []}


@router.get("/image/{filename}", summary="Stream Authentic Satellite Image File")
def get_satellite_image(filename: str):
    """Safely stream an authentic NASA/NOAA satellite infrared image frame."""
    # Sanitize filename
    safe_name = Path(filename).name
    img_path = IMAGES_DIR / safe_name
    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(status_code=404, detail="Satellite image file not found.")
    return FileResponse(img_path, media_type="image/jpeg")


@router.get("/insat_evaluations", summary="Retrieve Authentic INSAT Cross-Domain Evaluation Ledger")
def get_insat_evaluations() -> dict[str, Any]:
    """Retrieve verified zero-shot cross-sensor evaluation results on authentic INSAT crops."""
    ledger_path = MODELS_DIR / "insat_cross_domain_evaluation.json"
    if not ledger_path.exists():
        raise HTTPException(status_code=404, detail="INSAT evaluation ledger not found.")
    try:
        return json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to read INSAT evaluation ledger: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
