"""Synchronize demo cache forecasts with canonical benchmark outputs."""

import json
from pathlib import Path

biparjoy_canonical = {
    "storm_id": "2023156N10067",
    "storm_sid": "2023156N10067",
    "storm_name": "BIPARJOY",
    "season_year": 2023,
    "primary_basin": "Arabian Sea (AS)",
    "source_agency": "IMD",
    "wind_averaging_period": "3-min",
    "issue_time_utc": "2023-06-11T06:00:00Z",
    "input_observation_count": 43,
    "current_latitude": 18.3,
    "current_longitude": 67.8,
    "current_wind_speed_knots": 90.0,
    "current_imd_category": "Extremely Severe Cyclonic Storm (ESCS)",
    "estimated_speed_kmh": 11.2,
    "estimated_bearing_deg": 18.4,
    "forecast_points": [
        {
            "lead_time_hours": 6,
            "valid_time_utc": "2023-06-11T12:00:00Z",
            "predicted_latitude": 18.6,
            "predicted_longitude": 67.9,
            "predicted_wind_speed_knots": 90.0,
            "predicted_imd_category": "Extremely Severe Cyclonic Storm (ESCS)",
            "uncertainty_radius_km": 50.0,
        },
        {
            "lead_time_hours": 12,
            "valid_time_utc": "2023-06-11T18:00:00Z",
            "predicted_latitude": 19.0,
            "predicted_longitude": 68.1,
            "predicted_wind_speed_knots": 90.0,
            "predicted_imd_category": "Extremely Severe Cyclonic Storm (ESCS)",
            "uncertainty_radius_km": 85.0,
        },
        {
            "lead_time_hours": 24,
            "valid_time_utc": "2023-06-12T06:00:00Z",
            "predicted_latitude": 19.8,
            "predicted_longitude": 68.5,
            "predicted_wind_speed_knots": 90.0,
            "predicted_imd_category": "Extremely Severe Cyclonic Storm (ESCS)",
            "uncertainty_radius_km": 140.0,
        },
    ],
    "verification": [
        {
            "lead_time_hours": 6,
            "valid_time_utc": "2023-06-11T12:00:00Z",
            "predicted_latitude": 18.6,
            "predicted_longitude": 67.9,
            "actual_latitude": 18.6,
            "actual_longitude": 67.7,
            "track_error_km": 21.1,
            "predicted_wind_kt": 90.0,
            "actual_wind_kt": 90.0,
            "wind_error_kt": 0.0,
            "actual_category": "Extremely Severe Cyclonic Storm (ESCS)",
        },
        {
            "lead_time_hours": 12,
            "valid_time_utc": "2023-06-11T18:00:00Z",
            "predicted_latitude": 19.0,
            "predicted_longitude": 68.1,
            "actual_latitude": 18.9,
            "actual_longitude": 67.7,
            "track_error_km": 43.7,
            "predicted_wind_kt": 90.0,
            "actual_wind_kt": 90.0,
            "wind_error_kt": 0.0,
            "actual_category": "Extremely Severe Cyclonic Storm (ESCS)",
        },
        {
            "lead_time_hours": 24,
            "valid_time_utc": "2023-06-12T06:00:00Z",
            "predicted_latitude": 19.8,
            "predicted_longitude": 68.5,
            "actual_latitude": 19.6,
            "actual_longitude": 67.6,
            "track_error_km": 97.5,
            "predicted_wind_kt": 90.0,
            "actual_wind_kt": 85.0,
            "wind_error_kt": 5.0,
            "actual_category": "Extremely Severe Cyclonic Storm (ESCS)",
        },
    ],
    "mean_track_error_km": 54.1,
    "methodology": "Geodesic Constant-Velocity Extrapolation + Persistence/Bounded Intensity Trend",
    "limitations": "Deterministic kinematic reference model. Does not incorporate NWP atmospheric steering, vertical wind shear, or sea-surface temperatures.",
}

# Write to both BIPARJOY_forecast.json and 2023156N10067_forecast.json
cache_dir = Path("data/demo_cache/forecasts")
for name in ["BIPARJOY_forecast.json", "2023156N10067_forecast.json"]:
    f = cache_dir / name
    f.write_text(json.dumps(biparjoy_canonical, indent=2), encoding="utf-8")
    print(f"Updated {f}")
