"""Inference engine for VayumargTrackGRU.

Loads verified checkpoint, prepares sequence features from storm fixes,
and generates multi-horizon track displacements (+6h, +12h, +24h) and intensity forecasts
alongside geodesic and persistence baselines.
"""

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from vayumarg.ml.track.dataset import dxdy_to_latlon, haversine_km, latlon_to_dxdy_km
from vayumarg.ml.track.models import VayumargHybridTrackModel, VayumargTrackGRU


class TrackInferenceEngine:
    """Production inference engine for cyclone trajectory and intensity forecasting."""

    def __init__(self, checkpoint_path: str | Path | None = None, device: str | None = None):
        self.device = torch.device(
            device if device else ("cuda:0" if torch.cuda.is_available() else "cpu")
        )
        if checkpoint_path is None:
            checkpoint_path = Path("models/vayumarg/track_gru_best.pt")
        self.checkpoint_path = Path(checkpoint_path)
        self.model: VayumargTrackGRU | None = None
        self.sha256: str | None = None

        self.hybrid_model: VayumargHybridTrackModel | None = None
        self.hybrid_sha256: str | None = None
        self._load_model()
        self._load_hybrid_model()

    def _load_model(self) -> None:
        if not self.checkpoint_path.exists():
            return

        h = hashlib.sha256()
        with open(self.checkpoint_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        self.sha256 = h.hexdigest()

        # Load track GRU with strict weights_only=True (zero unpickling risk)
        ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=True)
        self.model = VayumargTrackGRU(
            in_features=ckpt.get("in_features", 10),
            hidden_size=ckpt.get("hidden_size", 96),
            num_layers=ckpt.get("num_layers", 2),
            horizons=tuple(ckpt.get("horizons", [6, 12, 24])),
        )
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

    def _load_hybrid_model(self) -> None:
        hybrid_path = self.checkpoint_path.parent / "track_hybrid_residual_best.pt"
        if not hybrid_path.exists():
            return

        h = hashlib.sha256()
        with open(hybrid_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        self.hybrid_sha256 = h.hexdigest()

        try:
            # Safe weights_only unpickling with minimal trusted NumPy scalar/dtype allowlist
            numpy_globals = [
                np.dtype,
                getattr(getattr(np, "dtypes", None), "Float64DType", float),
                getattr(getattr(np, "_core", None), "multiarray", getattr(np, "core", None)).scalar,
            ]
            with torch.serialization.safe_globals(numpy_globals):
                ckpt_h = torch.load(hybrid_path, map_location=self.device, weights_only=True)
            self.hybrid_model = VayumargHybridTrackModel(
                in_features=10,
                hidden_size=64,
                num_layers=2,
                horizons=(6, 12, 24),
            )
            self.hybrid_model.load_state_dict(ckpt_h["model_state_dict"])
            self.hybrid_model.to(self.device)
            self.hybrid_model.eval()
        except Exception:
            self.hybrid_model = None

    def is_ready(self) -> bool:
        return self.model is not None

    def predict(
        self,
        historical_fixes: list[dict[str, Any]],
        future_fixes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate multi-horizon forecast from at least 2 historical fixes.

        Args:
            historical_fixes: List of dicts with 'lat', 'lon', 'wind_kt' (optional 'time').
                              Chronological order, latest fix is current observation.
            future_fixes: Optional true future observations for ground-truth comparison.
        """
        if not self.is_ready():
            raise RuntimeError(
                f"Track GRU checkpoint not loaded from {self.checkpoint_path}. Ensure model is trained."
            )

        if len(historical_fixes) < 2:
            raise ValueError("Need at least 2 chronological fixes to forecast trajectory.")

        # Use up to 8 recent fixes; if fewer, pad by repeating earliest fix
        seq = historical_fixes[-8:]
        while len(seq) < 8:
            seq = [seq[0]] + seq

        # Build feature matrix [1, 8, 10]
        feat = np.zeros((1, 8, 10), dtype=np.float32)
        for t in range(8):
            curr = seq[t]
            prev = seq[t - 1] if t > 0 else seq[t]

            dx_prev, dy_prev = latlon_to_dxdy_km(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
            step_dt_h = 3.0 if t > 0 else 1.0
            speed_kmh = math.sqrt(dx_prev**2 + dy_prev**2) / step_dt_h
            bearing = math.atan2(dx_prev, dy_prev) if (dx_prev != 0 or dy_prev != 0) else 0.0
            delta_wind = curr["wind_kt"] - prev["wind_kt"]

            feat[0, t, 0] = curr["lat"] / 30.0
            feat[0, t, 1] = (curr["lon"] - 75.0) / 30.0
            feat[0, t, 2] = dx_prev / 50.0
            feat[0, t, 3] = dy_prev / 50.0
            feat[0, t, 4] = speed_kmh / 50.0
            feat[0, t, 5] = math.sin(bearing)
            feat[0, t, 6] = math.cos(bearing)
            feat[0, t, 7] = curr["wind_kt"] / 150.0
            feat[0, t, 8] = delta_wind / 10.0
            feat[0, t, 9] = float(t) / 7.0

        origin = seq[-1]
        o_lat = float(origin["lat"])
        o_lon = float(origin["lon"])
        o_wind = float(origin["wind_kt"])

        # Run model inference
        tensor_in = torch.from_numpy(feat).to(self.device)
        with torch.no_grad():
            out = self.model(tensor_in)
            pred_disp = out["displacement_km"].cpu().numpy()[0]  # [3, 2]
            pred_wind = out["future_wind_kt"].cpu().numpy()[0]  # [3]

        # Geodesic velocity from last 2 actual fixes
        penultimate = historical_fixes[-2]
        ultimate = historical_fixes[-1]
        last_dx, last_dy = latlon_to_dxdy_km(
            penultimate["lat"], penultimate["lon"], ultimate["lat"], ultimate["lon"]
        )
        vel_x = last_dx / 3.0
        vel_y = last_dy / 3.0

        # Base geodesic displacements for horizons [6, 12, 24]
        base_geo_np = np.array(
            [[vel_x * 6.0, vel_y * 6.0], [vel_x * 12.0, vel_y * 12.0], [vel_x * 24.0, vel_y * 24.0]],
            dtype=np.float32,
        )

        hyb_disp = None
        if self.hybrid_model is not None:
            base_geo_t = torch.from_numpy(base_geo_np).unsqueeze(0).to(self.device)
            with torch.no_grad():
                out_h = self.hybrid_model(tensor_in, base_geo_t)
                hyb_disp = out_h["final_disp_km"].cpu().numpy()[0]  # [3, 2]

        horizons = [6, 12, 24]
        predictions = []

        for h_idx, h in enumerate(horizons):
            # GRU predicted position
            p_dx = float(pred_disp[h_idx, 0])
            p_dy = float(pred_disp[h_idx, 1])
            p_lat, p_lon = dxdy_to_latlon(o_lat, o_lon, p_dx, p_dy)
            p_wind = float(pred_wind[h_idx])

            # Geodesic baseline
            g_dx = vel_x * h
            g_dy = vel_y * h
            g_lat, g_lon = dxdy_to_latlon(o_lat, o_lon, g_dx, g_dy)

            item = {
                "horizon_h": h,
                "gru_predicted": {
                    "latitude": round(p_lat, 2),
                    "longitude": round(p_lon, 2),
                    "dx_km": round(p_dx, 1),
                    "dy_km": round(p_dy, 1),
                    "displacement_total_km": round(math.sqrt(p_dx**2 + p_dy**2), 1),
                    "wind_speed_kt": round(p_wind, 1),
                },
                "geodesic_baseline": {
                    "latitude": round(g_lat, 2),
                    "longitude": round(g_lon, 2),
                    "dx_km": round(g_dx, 1),
                    "dy_km": round(g_dy, 1),
                    "displacement_total_km": round(math.sqrt(g_dx**2 + g_dy**2), 1),
                    "wind_speed_kt": round(o_wind, 1),
                },
            }

            # Hybrid predicted position
            if hyb_disp is not None:
                h_dx = float(hyb_disp[h_idx, 0])
                h_dy = float(hyb_disp[h_idx, 1])
                h_lat, h_lon = dxdy_to_latlon(o_lat, o_lon, h_dx, h_dy)
                item["hybrid_predicted"] = {
                    "latitude": round(h_lat, 2),
                    "longitude": round(h_lon, 2),
                    "dx_km": round(h_dx, 1),
                    "dy_km": round(h_dy, 1),
                    "displacement_total_km": round(math.sqrt(h_dx**2 + h_dy**2), 1),
                    "wind_speed_kt": round(p_wind, 1),
                }

            # If future ground truth is provided, compute verification metrics
            if future_fixes and h_idx < len(future_fixes):
                actual = future_fixes[h_idx]
                act_lat = float(actual["lat"])
                act_lon = float(actual["lon"])
                act_wind = float(actual["wind_kt"])

                err_gru = haversine_km(p_lat, p_lon, act_lat, act_lon)
                err_geo = haversine_km(g_lat, g_lon, act_lat, act_lon)
                err_stat = haversine_km(o_lat, o_lon, act_lat, act_lon)

                ver_dict = {
                    "gru_track_error_km": round(err_gru, 1),
                    "geodesic_track_error_km": round(err_geo, 1),
                    "stationary_track_error_km": round(err_stat, 1),
                    "gru_wind_error_kt": round(abs(p_wind - act_wind), 1),
                    "persistence_wind_error_kt": round(abs(o_wind - act_wind), 1),
                    "skill_score_vs_geodesic": round(1.0 - (err_gru / max(0.1, err_geo)), 3),
                }

                if hyb_disp is not None:
                    h_lat_val = item["hybrid_predicted"]["latitude"]
                    h_lon_val = item["hybrid_predicted"]["longitude"]
                    err_hyb = haversine_km(h_lat_val, h_lon_val, act_lat, act_lon)
                    ver_dict["hybrid_track_error_km"] = round(err_hyb, 1)
                    ver_dict["hybrid_improvement_over_geodesic_km"] = round(err_geo - err_hyb, 1)

                item["ground_truth"] = {
                    "latitude": round(act_lat, 2),
                    "longitude": round(act_lon, 2),
                    "wind_speed_kt": round(act_wind, 1),
                }
                item["verification"] = ver_dict

            predictions.append(item)

        return {
            "model_id": "vayumarg-track-gru-v1",
            "model_type": "Recurrent Spatiotemporal GRU with Temporal Attention",
            "sha256": self.sha256,
            "hybrid_sha256": self.hybrid_sha256,
            "origin_fix": {
                "latitude": round(o_lat, 2),
                "longitude": round(o_lon, 2),
                "wind_speed_kt": round(o_wind, 1),
            },
            "horizons": horizons,
            "forecasts": predictions,
        }
