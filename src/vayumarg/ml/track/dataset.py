"""Dataset and sliding window generation for Cyclone Track & Wind Forecasting.

Processes historical IBTrACS North Indian Ocean tracks into normalized
spatiotemporal sequence tensors for recurrent neural network training and evaluation.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


@dataclass
class TrackFix:
    """Single observation fix of a tropical cyclone."""

    time: datetime
    lat: float
    lon: float
    wind_kt: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two geographic coordinates in kilometers."""
    r_earth = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def latlon_to_dxdy_km(
    origin_lat: float, origin_lon: float, target_lat: float, target_lon: float
) -> tuple[float, float]:
    """Convert spherical delta from origin to target into local (dx, dy) in kilometers."""
    dy = (target_lat - origin_lat) * 111.12
    dx = (target_lon - origin_lon) * 111.12 * math.cos(math.radians(origin_lat))
    return dx, dy


def dxdy_to_latlon(
    origin_lat: float, origin_lon: float, dx: float, dy: float
) -> tuple[float, float]:
    """Convert local (dx, dy) in kilometers back to geographic (lat, lon)."""
    target_lat = origin_lat + (dy / 111.12)
    cos_lat = math.cos(math.radians(origin_lat))
    if abs(cos_lat) < 1e-6:
        cos_lat = 1e-6
    target_lon = origin_lon + (dx / (111.12 * cos_lat))
    return target_lat, target_lon


class CycloneTrackDataset(Dataset):
    """PyTorch Dataset yielding historical track windows and multi-horizon targets."""

    def __init__(
        self,
        samples: list[dict[str, np.ndarray]],
    ):
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        sample = self.samples[idx]
        return {
            "features": torch.from_numpy(sample["features"]).float(),
            "target_disp": torch.from_numpy(sample["target_disp"]).float(),
            "target_wind": torch.from_numpy(sample["target_wind"]).float(),
            "origin_lat": torch.tensor(sample["origin_lat"], dtype=torch.float32),
            "origin_lon": torch.tensor(sample["origin_lon"], dtype=torch.float32),
            "target_latlon": torch.from_numpy(sample["target_latlon"]).float(),
            "baseline_geodesic_disp": torch.from_numpy(sample["baseline_geodesic_disp"]).float(),
            "baseline_persistence_wind": torch.from_numpy(
                sample["baseline_persistence_wind"]
            ).float(),
        }


def load_ibtracs_storms(
    csv_path: str | Path,
    min_year: int = 1980,
) -> dict[str, dict]:
    """Parse IBTrACS CSV into clean storm records."""
    import csv

    storms: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader)  # Header
        _ = next(reader)  # Units
        for row in reader:
            if len(row) < 24:
                continue
            sid = row[0].strip()
            season_str = row[1].strip()
            season = int(season_str) if season_str.isdigit() else 0
            if season < min_year:
                continue

            name = row[5].strip()
            iso_time = row[6].strip()
            lat_str = row[8].strip()
            lon_str = row[9].strip()
            wmo_wind = row[10].strip()
            usa_wind = row[23].strip()

            if not lat_str or not lon_str:
                continue
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                dt = datetime.strptime(iso_time, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                continue

            wind = None
            for w in [wmo_wind, usa_wind]:
                if w and w != " ":
                    try:
                        wind = float(w)
                        break
                    except ValueError:
                        pass
            if wind is None:
                wind = 30.0

            if sid not in storms:
                storms[sid] = {
                    "sid": sid,
                    "season": season,
                    "name": name,
                    "fixes": [],
                }
            storms[sid]["fixes"].append(TrackFix(time=dt, lat=lat, lon=lon, wind_kt=wind))

    # Sort fixes by time for each storm
    for sid in storms:
        storms[sid]["fixes"].sort(key=lambda fix: fix.time)

    return storms


def extract_sliding_windows(
    storms: dict[str, dict],
    in_steps: int = 8,
    target_horizons_h: tuple[int, ...] = (6, 12, 24),
) -> list[dict[str, np.ndarray]]:
    """Extract regular 3-hourly sliding sequence windows and target horizons.

    Target steps corresponding to 3h intervals:
    +6h  -> +2 steps
    +12h -> +4 steps
    +24h -> +8 steps
    Total sequence length needed: in_steps + max(target_steps) = 8 + 8 = 16 fixes.
    """
    target_steps = [h // 3 for h in target_horizons_h]
    max_target_step = max(target_steps)
    total_window_len = in_steps + max_target_step

    samples: list[dict[str, np.ndarray]] = []

    for sid, storm in storms.items():
        fixes: list[TrackFix] = storm["fixes"]
        if len(fixes) < total_window_len:
            continue

        for i in range(len(fixes) - total_window_len + 1):
            # Verify consecutive 3h intervals within tolerance (<= 0.5h deviation)
            window_fixes = fixes[i : i + total_window_len]
            valid_dt = True
            for k in range(total_window_len - 1):
                dt_h = (window_fixes[k + 1].time - window_fixes[k].time).total_seconds() / 3600.0
                if abs(dt_h - 3.0) > 0.5:
                    valid_dt = False
                    break
            if not valid_dt:
                continue

            # Historical inputs: [0 ... in_steps - 1]
            hist = window_fixes[:in_steps]
            origin_fix = hist[-1]
            origin_lat = origin_fix.lat
            origin_lon = origin_fix.lon
            origin_wind = origin_fix.wind_kt

            # Compute input features for each historical step: 10 features
            feature_matrix = np.zeros((in_steps, 10), dtype=np.float32)
            for t in range(in_steps):
                curr = hist[t]
                prev = hist[t - 1] if t > 0 else hist[t]

                # Displacement relative to previous step in km
                dx_prev, dy_prev = latlon_to_dxdy_km(prev.lat, prev.lon, curr.lat, curr.lon)
                step_dt_h = 3.0 if t > 0 else 1.0
                speed_kmh = math.sqrt(dx_prev**2 + dy_prev**2) / step_dt_h
                bearing = math.atan2(dx_prev, dy_prev) if (dx_prev != 0 or dy_prev != 0) else 0.0
                delta_wind = curr.wind_kt - prev.wind_kt

                # 1. lat normalized
                feature_matrix[t, 0] = curr.lat / 30.0
                # 2. lon normalized
                feature_matrix[t, 1] = (curr.lon - 75.0) / 30.0
                # 3. dx_prev (normalized by 50 km)
                feature_matrix[t, 2] = dx_prev / 50.0
                # 4. dy_prev (normalized by 50 km)
                feature_matrix[t, 3] = dy_prev / 50.0
                # 5. speed_kmh (normalized by 50 km/h)
                feature_matrix[t, 4] = speed_kmh / 50.0
                # 6. bearing sine
                feature_matrix[t, 5] = math.sin(bearing)
                # 7. bearing cosine
                feature_matrix[t, 6] = math.cos(bearing)
                # 8. wind_kt (normalized by 150 kt)
                feature_matrix[t, 7] = curr.wind_kt / 150.0
                # 9. delta_wind (normalized by 10 kt)
                feature_matrix[t, 8] = delta_wind / 10.0
                # 10. relative progression index [0, 1]
                feature_matrix[t, 9] = float(t) / float(in_steps - 1)

            # Targets: for each horizon in target_steps
            target_disp = np.zeros((len(target_steps), 2), dtype=np.float32)
            target_wind = np.zeros((len(target_steps),), dtype=np.float32)
            target_latlon = np.zeros((len(target_steps), 2), dtype=np.float32)
            baseline_geodesic_disp = np.zeros((len(target_steps), 2), dtype=np.float32)
            baseline_persistence_wind = np.zeros((len(target_steps),), dtype=np.float32)

            # Geodesic baseline velocity estimate from last 2 historical fixes (over 3h)
            last_dx, last_dy = latlon_to_dxdy_km(hist[-2].lat, hist[-2].lon, origin_lat, origin_lon)
            vel_x_km_per_h = last_dx / 3.0
            vel_y_km_per_h = last_dy / 3.0

            for h_idx, step_offset in enumerate(target_steps):
                future_fix = window_fixes[in_steps - 1 + step_offset]
                fdx, fdy = latlon_to_dxdy_km(origin_lat, origin_lon, future_fix.lat, future_fix.lon)
                target_disp[h_idx, 0] = fdx
                target_disp[h_idx, 1] = fdy
                target_wind[h_idx] = future_fix.wind_kt
                target_latlon[h_idx, 0] = future_fix.lat
                target_latlon[h_idx, 1] = future_fix.lon

                horizon_h = target_horizons_h[h_idx]
                baseline_geodesic_disp[h_idx, 0] = vel_x_km_per_h * horizon_h
                baseline_geodesic_disp[h_idx, 1] = vel_y_km_per_h * horizon_h
                baseline_persistence_wind[h_idx] = origin_wind

            samples.append(
                {
                    "sid": sid,
                    "name": storm["name"],
                    "features": feature_matrix,
                    "target_disp": target_disp,
                    "target_wind": target_wind,
                    "origin_lat": origin_lat,
                    "origin_lon": origin_lon,
                    "target_latlon": target_latlon,
                    "baseline_geodesic_disp": baseline_geodesic_disp,
                    "baseline_persistence_wind": baseline_persistence_wind,
                }
            )

    return samples


def split_storm_disjoint(
    storms: dict[str, dict],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    """Split storm dictionary by storm SID into train, validation, and test subsets."""
    rng = np.random.RandomState(seed)
    sids = sorted(storms.keys())
    rng.shuffle(sids)

    n_total = len(sids)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_sids = set(sids[:n_train])
    val_sids = set(sids[n_train : n_train + n_val])
    test_sids = set(sids[n_train + n_val :])

    train_storms = {sid: storms[sid] for sid in train_sids}
    val_storms = {sid: storms[sid] for sid in val_sids}
    test_storms = {sid: storms[sid] for sid in test_sids}

    return train_storms, val_storms, test_storms
