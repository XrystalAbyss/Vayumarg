"""Module B: Reproducible Geodesic Constant-Velocity Track Forecasting & Persistence Intensity Baseline.

Provides transparent, physically bounded forecast calculations without unverified ML black boxes:
1. Great-circle / Haversine forward velocity estimation from valid historical observations strictly UP TO issue time.
2. Geodesic forward extrapolation along rhumb-line / great-circle trajectory at +6h, +12h, +24h horizons.
3. Persistence and bounded-trend wind intensity forecasting.
4. Independent hindsight verification against subsequent ground-truth fixes (without predictive data leakage).
"""

import math
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from vayumarg.satellite.alignment import calculate_haversine_distance_km

EARTH_RADIUS_KM = 6371.0


class ForecastPoint(BaseModel):
    lead_time_hours: int
    valid_time_utc: datetime
    predicted_latitude: float
    predicted_longitude: float
    predicted_wind_speed_knots: float
    predicted_imd_category: str
    uncertainty_radius_km: float


class HindsightVerificationPoint(BaseModel):
    lead_time_hours: int
    valid_time_utc: datetime
    predicted_latitude: float
    predicted_longitude: float
    actual_latitude: float | None = None
    actual_longitude: float | None = None
    track_error_km: float | None = None
    predicted_wind_kt: float
    actual_wind_kt: float | None = None
    wind_error_kt: float | None = None
    actual_category: str | None = None


class CycloneForecastResult(BaseModel):
    storm_id: str
    storm_name: str
    issue_time_utc: datetime
    input_observation_count: int
    current_latitude: float
    current_longitude: float
    current_wind_speed_knots: float | None
    current_imd_category: str | None
    estimated_speed_kmh: float
    estimated_bearing_deg: float
    forecast_points: list[ForecastPoint]
    verification: list[HindsightVerificationPoint]
    methodology: str = (
        "Geodesic Constant-Velocity Extrapolation + Persistence/Bounded Intensity Trend"
    )
    limitations: str = "Baseline meteorological reference model. Does not incorporate NWP atmospheric steering, vertical wind shear, or sea-surface temperatures."


def classify_imd_category(wind_kt: float | None) -> str:
    """Classify 3-minute sustained wind into IMD cyclone categories."""
    if wind_kt is None or math.isnan(wind_kt):
        return "Unknown"
    if wind_kt < 17:
        return "Low Pressure Area"
    elif wind_kt < 28:
        return "Depression (D)"
    elif wind_kt < 34:
        return "Deep Depression (DD)"
    elif wind_kt < 48:
        return "Cyclonic Storm (CS)"
    elif wind_kt < 64:
        return "Severe Cyclonic Storm (SCS)"
    elif wind_kt < 90:
        return "Very Severe Cyclonic Storm (VSCS)"
    elif wind_kt < 120:
        return "Extremely Severe Cyclonic Storm (ESCS)"
    else:
        return "Super Cyclonic Storm (SuCS)"


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate initial compass bearing from (lat1, lon1) to (lat2, lon2) in degrees."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(y, x)
    return (math.degrees(bearing_rad) + 360.0) % 360.0


def extrapolate_geodesic(
    lat: float, lon: float, bearing_deg: float, distance_km: float
) -> tuple[float, float]:
    """Calculate destination point given start point, initial bearing and distance."""
    delta = distance_km / EARTH_RADIUS_KM
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)

    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )

    # Normalize longitude to [-180, 180]
    lat2 = math.degrees(phi2)
    lon2 = (math.degrees(lambda2) + 540.0) % 360.0 - 180.0
    return round(lat2, 2), round(lon2, 2)


def compute_cyclone_forecast(
    storm_id: str,
    storm_name: str,
    observations: list[dict[str, Any]],
    issue_time_utc: datetime,
    horizons_hours: list[int] | None = None,
) -> CycloneForecastResult:
    """Compute reproducible forecast baseline given observations strictly up to issue_time_utc.

    observations must be dicts with:
      - observation_time_utc (datetime)
      - latitude (float)
      - longitude (float)
      - wind_speed_knots (float | None)
      - imd_category (str | None)
    """
    if horizons_hours is None:
        horizons_hours = [6, 12, 24]

    def _parse_dt(val: Any) -> datetime:
        if isinstance(val, datetime):
            return val if val.tzinfo is not None else val.replace(tzinfo=UTC)
        s = str(val).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    # Normalize issue_time_utc
    if issue_time_utc.tzinfo is None:
        issue_time_utc = issue_time_utc.replace(tzinfo=UTC)

    # Normalize observation times and partition
    normalized_obs = []
    for o in observations:
        if o.get("latitude") is None or o.get("longitude") is None:
            continue
        item = dict(o)
        item["_dt"] = _parse_dt(item["observation_time_utc"])
        normalized_obs.append(item)

    # Partition historical input strictly <= issue_time_utc and future verification > issue_time_utc
    history = [o for o in normalized_obs if o["_dt"] <= issue_time_utc]
    history.sort(key=lambda x: x["_dt"])

    if len(history) < 2:
        raise ValueError(
            f"Insufficient historical track points prior to {issue_time_utc}. Need at least 2 consecutive fixes, found {len(history)}."
        )

    # Future ground truth fixes strictly for hindsight verification
    future_ground_truth = [o for o in normalized_obs if o["_dt"] > issue_time_utc]
    future_ground_truth.sort(key=lambda x: x["_dt"])

    # Current state at issue time (most recent observation)
    curr = history[-1]
    prev = history[-2]

    curr_lat, curr_lon = float(curr["latitude"]), float(curr["longitude"])
    prev_lat, prev_lon = float(prev["latitude"]), float(prev["longitude"])
    curr_time = curr["_dt"]
    prev_time = prev["_dt"]

    delta_hours = (curr_time - prev_time).total_seconds() / 3600.0
    if delta_hours <= 0:
        delta_hours = 3.0  # Synoptic fallback

    # Compute velocity vector
    dist_step_km = calculate_haversine_distance_km(prev_lat, prev_lon, curr_lat, curr_lon)
    speed_kmh = dist_step_km / delta_hours
    bearing_deg = calculate_bearing_deg(prev_lat, prev_lon, curr_lat, curr_lon)

    # Wind intensity and recent trend
    curr_wind = (
        float(curr["wind_speed_knots"]) if curr.get("wind_speed_knots") is not None else 35.0
    )
    prev_wind = (
        float(prev["wind_speed_knots"]) if prev.get("wind_speed_knots") is not None else curr_wind
    )
    wind_trend_per_hour = (curr_wind - prev_wind) / delta_hours if delta_hours > 0 else 0.0
    # Bound trend to realistic meteorological rates (-5 to +5 kt/h)
    bounded_trend = max(-5.0, min(5.0, wind_trend_per_hour))

    # Calculate forecast steps
    forecast_points: list[ForecastPoint] = []
    verification_points: list[HindsightVerificationPoint] = []

    # Uncertainty radii roughly calibrated to North Indian Ocean operational track errors:
    # +6h ~ 50 km, +12h ~ 85 km, +24h ~ 140 km
    uncertainty_map = {6: 50.0, 12: 85.0, 24: 140.0}

    for h in horizons_hours:
        proj_time = issue_time_utc + timedelta(hours=h)
        proj_dist_km = speed_kmh * h
        pred_lat, pred_lon = extrapolate_geodesic(curr_lat, curr_lon, bearing_deg, proj_dist_km)

        # Dampen trend as horizon expands: 70% trend at +6h, 40% at +12h, 10% at +24h
        damping = max(0.0, 1.0 - (h / 30.0))
        pred_wind = max(15.0, min(170.0, curr_wind + (bounded_trend * h * damping)))
        pred_cat = classify_imd_category(pred_wind)
        uncert = uncertainty_map.get(h, 40.0 + (h * 4.5))

        f_pt = ForecastPoint(
            lead_time_hours=h,
            valid_time_utc=proj_time,
            predicted_latitude=pred_lat,
            predicted_longitude=pred_lon,
            predicted_wind_speed_knots=round(pred_wind, 1),
            predicted_imd_category=pred_cat,
            uncertainty_radius_km=round(uncert, 1),
        )
        forecast_points.append(f_pt)

        # Hindsight verification: Find closest actual observation within 3 hours of valid_time_utc
        actual_match = None
        best_diff_h = 3.001
        for gt in future_ground_truth:
            diff_h = abs((gt["_dt"] - proj_time).total_seconds()) / 3600.0
            if diff_h <= 3.0 and diff_h < best_diff_h:
                best_diff_h = diff_h
                actual_match = gt

        if actual_match:
            act_lat = float(actual_match["latitude"])
            act_lon = float(actual_match["longitude"])
            err_km = calculate_haversine_distance_km(pred_lat, pred_lon, act_lat, act_lon)
            act_w = (
                float(actual_match["wind_speed_knots"])
                if actual_match.get("wind_speed_knots") is not None
                else None
            )
            w_err = abs(pred_wind - act_w) if act_w is not None else None
            act_cat = actual_match.get("imd_category") or classify_imd_category(act_w)

            verification_points.append(
                HindsightVerificationPoint(
                    lead_time_hours=h,
                    valid_time_utc=proj_time,
                    predicted_latitude=pred_lat,
                    predicted_longitude=pred_lon,
                    actual_latitude=act_lat,
                    actual_longitude=act_lon,
                    track_error_km=round(err_km, 1),
                    predicted_wind_kt=round(pred_wind, 1),
                    actual_wind_kt=round(act_w, 1) if act_w is not None else None,
                    wind_error_kt=round(w_err, 1) if w_err is not None else None,
                    actual_category=act_cat,
                )
            )
        else:
            verification_points.append(
                HindsightVerificationPoint(
                    lead_time_hours=h,
                    valid_time_utc=proj_time,
                    predicted_latitude=pred_lat,
                    predicted_longitude=pred_lon,
                    predicted_wind_kt=round(pred_wind, 1),
                )
            )

    return CycloneForecastResult(
        storm_id=storm_id,
        storm_name=storm_name,
        issue_time_utc=issue_time_utc,
        input_observation_count=len(history),
        current_latitude=curr_lat,
        current_longitude=curr_lon,
        current_wind_speed_knots=round(curr_wind, 1),
        current_imd_category=curr.get("imd_category") or classify_imd_category(curr_wind),
        estimated_speed_kmh=round(speed_kmh, 1),
        estimated_bearing_deg=round(bearing_deg, 1),
        forecast_points=forecast_points,
        verification=verification_points,
    )
