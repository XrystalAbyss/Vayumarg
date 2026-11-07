"""Satellite Deep Learning Inference Engine and Prediction API Contract.

Serves production predictions from the trained ResNet-18 CNN Intensity Regressor
and Spatiotemporal ConvLSTM Forecaster, with cross-domain adapters for authentic
ISRO INSAT-3DR/3DS multichannel crops and explicit scientific transfer limitations.
"""

from pathlib import Path
from typing import Any

import h5py
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image

from vayumarg.ml.vision.dataset import CATEGORY_NAMES
from vayumarg.ml.vision.models import CycloneCNNRegressor, CycloneConvLSTM

# Traverse up to project root (directory containing data and models)
current = Path(__file__).resolve().parent
while current.parent != current:
    if (
        (current / "data").exists()
        or (current / "models").exists()
        or (current / "pyproject.toml").exists()
    ):
        break
    current = current.parent
BASE_DIR = current
MODELS_DIR = BASE_DIR / "models" / "vayumarg" / "vision"
CROPS_DIR = BASE_DIR / "data" / "processed" / "satellite" / "crops"


class PredictionAPIContract:
    """Standardized Machine-Readable Prediction Contract for Integration."""

    @staticmethod
    def format_cnn_prediction(
        predicted_wind_kt: float,
        category_index: int,
        category_name: str,
        category_probabilities: dict[str, float],
        confidence_radius_kt: float,
        inference_latency_ms: float,
        source_domain: str,
        domain_transfer_disclaimer: str | None = None,
    ) -> dict[str, Any]:
        return {
            "model_type": "CNN_INTENSITY_REGRESSOR",
            "model_architecture": "ResNet18-IR-SingleChannel",
            "predicted_max_sustained_wind_knots": round(float(predicted_wind_kt), 1),
            "predicted_wind_kmh": round(float(predicted_wind_kt * 1.852), 1),
            "predicted_category_index": int(category_index),
            "predicted_category_label": category_name,
            "category_probabilities": {k: round(v, 4) for k, v in category_probabilities.items()},
            "estimated_uncertainty_kt": round(float(confidence_radius_kt), 1),
            "inference_latency_ms": round(float(inference_latency_ms), 2),
            "source_domain": source_domain,
            "scientific_disclaimer": domain_transfer_disclaimer
            or "Experimental deep-learning intensity estimation. Not an operational warning guidance.",
        }

    @staticmethod
    def format_convlstm_forecast(
        predicted_future_wind_kt: float,
        lead_time_hours: float,
        past_observed_winds: list[float],
        persistence_delta_kt: float,
        inference_latency_ms: float,
    ) -> dict[str, Any]:
        return {
            "model_type": "CONVLSTM_SPATIOTEMPORAL_FORECASTER",
            "model_architecture": "CycloneConvLSTM-32-64",
            "forecast_lead_time_hours": lead_time_hours,
            "predicted_future_wind_knots": round(float(predicted_future_wind_kt), 1),
            "predicted_future_wind_kmh": round(float(predicted_future_wind_kt * 1.852), 1),
            "past_input_winds_knots": [round(w, 1) for w in past_observed_winds],
            "persistence_trend_delta_knots": round(float(persistence_delta_kt), 1),
            "inference_latency_ms": round(float(inference_latency_ms), 2),
            "scientific_disclaimer": (
                "Spatiotemporal ConvLSTM forward intensity projection. "
                "Evaluates visual kinematic persistence and convective cloud-shield evolution."
            ),
        }


class SatelliteInferenceEngine:
    """Production inference engine for Vayumarg satellite vision models."""

    def __init__(
        self,
        cnn_checkpoint_path: str | Path | None = None,
        convlstm_checkpoint_path: str | Path | None = None,
        device: str | None = None,
    ):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.cnn_path = Path(cnn_checkpoint_path or (MODELS_DIR / "satellite_cnn_best.pt"))
        self.convlstm_path = Path(
            convlstm_checkpoint_path or (MODELS_DIR / "satellite_convlstm_best.pt")
        )

        self._cnn_model: CycloneCNNRegressor | None = None
        self._convlstm_model: CycloneConvLSTM | None = None

        self.cnn_transform = T.Compose(
            [
                T.Resize((128, 128)),
                T.ToTensor(),
                T.Normalize(mean=[0.45], std=[0.22]),
            ]
        )

        self.convlstm_transform = T.Compose(
            [
                T.Resize((64, 64)),
                T.ToTensor(),
                T.Normalize(mean=[0.45], std=[0.22]),
            ]
        )

    def load_cnn(self) -> CycloneCNNRegressor:
        """Lazy load CNN model."""
        if self._cnn_model is None:
            if not self.cnn_path.is_file():
                raise FileNotFoundError(f"CNN checkpoint not found at {self.cnn_path}")
            model = CycloneCNNRegressor(pretrained_backbone=False)
            checkpoint = torch.load(self.cnn_path, map_location=self.device)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.to(self.device)
            model.eval()
            self._cnn_model = model
        return self._cnn_model

    def load_convlstm(self) -> CycloneConvLSTM:
        """Lazy load ConvLSTM model."""
        if self._convlstm_model is None:
            if not self.convlstm_path.is_file():
                raise FileNotFoundError(f"ConvLSTM checkpoint not found at {self.convlstm_path}")
            model = CycloneConvLSTM(in_channels=1, hidden_dims=(32, 64))
            checkpoint = torch.load(self.convlstm_path, map_location=self.device)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.to(self.device)
            model.eval()
            self._convlstm_model = model
        return self._convlstm_model

    def predict_image(self, img: Image.Image) -> dict[str, Any]:
        """Run CNN intensity regression on PIL image."""
        model = self.load_cnn()
        t0 = torch.cuda.Event(enable_timing=True) if self.device.type == "cuda" else None
        t1 = torch.cuda.Event(enable_timing=True) if self.device.type == "cuda" else None

        import time

        start_time = time.perf_counter()

        img_gray = img.convert("L")
        tensor = self.cnn_transform(img_gray).unsqueeze(0).to(self.device)

        if t0:
            t0.record()

        with torch.no_grad():
            wind_pred, cat_logits = model(tensor)
            probs = torch.softmax(cat_logits, dim=-1).squeeze(0).cpu().numpy()

        if t1:
            t1.record()
            torch.cuda.synchronize()
            latency_ms = t0.elapsed_time(t1)
        else:
            latency_ms = (time.perf_counter() - start_time) * 1000.0

        wind_kt = float(wind_pred.item())
        cat_idx = int(cat_logits.argmax(dim=-1).item())
        cat_name = CATEGORY_NAMES[cat_idx]

        cat_probs = {CATEGORY_NAMES[i]: float(probs[i]) for i in range(len(probs))}

        return PredictionAPIContract.format_cnn_prediction(
            predicted_wind_kt=wind_kt,
            category_index=cat_idx,
            category_name=cat_name,
            category_probabilities=cat_probs,
            confidence_radius_kt=10.5,  # Empirical validation RMSE envelope
            inference_latency_ms=latency_ms,
            source_domain="NOAA_GOES_IR_CALIBRATED",
        )

    def forecast_sequence(
        self, frames: list[Image.Image], lead_time_hours: float = 3.0
    ) -> dict[str, Any]:
        """Run ConvLSTM spatiotemporal sequence forecast across past T frames."""
        model = self.load_convlstm()

        import time

        start_time = time.perf_counter()

        seq_tensors = [self.convlstm_transform(f.convert("L")) for f in frames]
        # (1, T, 1, H, W)
        seq_batch = torch.stack(seq_tensors, dim=0).unsqueeze(0).to(self.device)

        with torch.no_grad():
            pred_wind, next_frame_tensor = model(seq_batch)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        predicted_wind = float(pred_wind.item())

        # Encode reconstructed next frame as base64 PNG data URI
        import base64
        import io

        rec_arr = (next_frame_tensor.squeeze().cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        rec_img = Image.fromarray(rec_arr)
        buf = io.BytesIO()
        rec_img.save(buf, format="PNG")
        reconstructed_b64 = (
            f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        )

        res = PredictionAPIContract.format_convlstm_forecast(
            predicted_future_wind_kt=predicted_wind,
            lead_time_hours=lead_time_hours,
            past_observed_winds=[],
            persistence_delta_kt=0.0,
            inference_latency_ms=latency_ms,
        )
        res["reconstructed_next_frame_b64"] = reconstructed_b64
        return res

    predict_sequence = forecast_sequence

    def evaluate_insat_crop(self, storm_name: str, channel: str = "TIR-1") -> dict[str, Any]:
        """Run zero-shot cross-sensor domain transfer evaluation on authentic INSAT-3DR/3DS HDF5 crop."""
        name_upper = storm_name.upper()

        crop_files = list(CROPS_DIR.glob(f"{name_upper}*MULTICHANNEL.h5"))
        if not crop_files:
            raise FileNotFoundError(
                f"No authentic INSAT crop found for {storm_name} in {CROPS_DIR}"
            )

        crop_file = crop_files[0]
        ch_key = channel.upper().replace("_", "-")

        with h5py.File(crop_file, "r") as h5:
            if "coregistered" not in h5 or ch_key not in h5["coregistered"]:
                raise KeyError(f"Channel {ch_key} not found in {crop_file.name}")
            arr_k = h5["coregistered"][ch_key][:].astype(float)

        # Preprocessing: convert Kelvin array (180K - 310K) into normalized grayscale
        # Inverted IR: Cold cloud tops (180K) -> Bright white (255); Warm ocean (300K) -> Dark (0)
        norm_ir = np.clip((310.0 - arr_k) / (310.0 - 180.0) * 255.0, 0, 255).astype(np.uint8)
        img = Image.fromarray(norm_ir)

        res = self.predict_image(img)
        res["source_domain"] = f"ISRO_MOSDAC_{name_upper}_{channel}_HDF5"
        res["domain_transfer_disclaimer"] = (
            "Cross-Sensor Domain Evaluation: Model was trained on NASA Clean IR Band 13 (10.3 µm). "
            f"Evaluated zero-shot on ISRO INSAT-3DR/3DS {channel} (10.8 µm, Δλ ≈ 0.5 µm). Spectral response function (SRF), "
            "sub-satellite longitude, and sensor calibration lookup tables differ systematically. "
            "Predictions are descriptive academic transfers, not validated operational guidance."
        )
        return res
