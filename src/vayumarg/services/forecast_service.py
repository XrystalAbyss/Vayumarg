"""Forecast generation, multi-horizon geodesic extrapolation, and hindsight verification service."""

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vayumarg.database.engine import get_db_session
from vayumarg.module_b.baseline import (
    compute_cyclone_forecast as compute_baseline_cyclone_forecast,
)
from vayumarg.module_b.contracts import (
    CycloneForecastOutput,
    HindsightVerificationOutput,
)
from vayumarg.module_b.forecast_engine import (
    generate_forecast_from_db,
    verify_forecast_from_db,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEMO_CACHE_DIR = BASE_DIR / "data" / "demo_cache"

DEMO_SCENARIOS = [
    {
        "case_id": "biparjoy_arabian_sea",
        "storm_name": "BIPARJOY",
        "storm_sid": "2023156N10067",
        "canonical_sid": "2023156N10067",
        "season_year": 2023,
        "primary_basin": "Arabian Sea (AS)",
        "source_agency": "IMD",
        "averaging_period": "3-min",
        "issue_time_utc": "2023-06-11T06:00:00Z",
        "stage": "Open-ocean intensification (4 days pre-landfall)",
        "earlier_observations_count": 43,
        "validation_horizons": [6, 12, 24],
        "rationale": (
            "Extremely Severe Cyclonic Storm BIPARJOY tracking northward over the central Arabian Sea. "
            "Evaluates geodesic extrapolation during quasi-linear steering before recurvature towards Gujarat."
        ),
    },
    {
        "case_id": "amphan_bay_of_bengal",
        "storm_name": "AMPHAN",
        "storm_sid": "2020136N10088",
        "canonical_sid": "2020136N10088",
        "season_year": 2020,
        "primary_basin": "Bay of Bengal (BB)",
        "source_agency": "IMD",
        "averaging_period": "3-min",
        "issue_time_utc": "2020-05-18T00:00:00Z",
        "stage": "Rapid intensification to Super Cyclone (2.5 days pre-landfall)",
        "earlier_observations_count": 17,
        "validation_horizons": [6, 12, 24],
        "rationale": (
            "Historic Super Cyclonic Storm AMPHAN tracking northward in central Bay of Bengal. "
            "Demonstrates persistence baseline and bounded-trend intensity forecasting during explosive deepening."
        ),
    },
    {
        "case_id": "remal_bay_of_bengal",
        "storm_name": "REMAL",
        "storm_sid": "2024145N14087",
        "canonical_sid": "2024145N14087",
        "season_year": 2024,
        "primary_basin": "Bay of Bengal (BB)",
        "source_agency": "IMD",
        "averaging_period": "3-min",
        "issue_time_utc": "2024-05-25T12:00:00Z",
        "stage": "Cyclonic storm translation over northern Bay of Bengal (30 hours pre-landfall)",
        "earlier_observations_count": 13,
        "validation_horizons": [6, 12, 24],
        "rationale": (
            "Severe Cyclonic Storm REMAL accelerating northward towards Bangladesh/West Bengal coast. "
            "Validates geodesic forward trajectory against tight synoptic 3-hourly verification fixes."
        ),
    },
]


class ForecastService:
    """Encapsulates forecast generation, geodesic forward projection, and hindsight evaluation."""

    @staticmethod
    def list_demo_cases() -> list[dict[str, Any]]:
        """Return pre-configured historical demonstration scenarios (BIPARJOY, AMPHAN, DANA, REMAL)."""
        scen_file = DEMO_CACHE_DIR / "scenarios.json"
        if scen_file.is_file():
            try:
                with open(scen_file, encoding="utf-8") as f:
                    cases = json.load(f)
                    for c in cases:
                        sid = c.get("canonical_sid") or c.get("storm_sid")
                        if sid:
                            c["canonical_sid"] = sid
                            c["storm_sid"] = sid
                    return cases
            except Exception:
                pass
        return DEMO_SCENARIOS

    @staticmethod
    def generate_forecast(
        storm_identifier: str,
        issue_time_utc: datetime,
        agency: str = "IMD",
        horizons_hours: list[int] | None = None,
    ) -> dict[str, Any]:
        """Generate deterministic Geodesic Constant-Velocity extrapolation forecast (+6h, +12h, +24h)."""
        if horizons_hours is None:
            horizons_hours = [6, 12, 24]

        forecast: CycloneForecastOutput | None = None
        verification: HindsightVerificationOutput | None = None

        try:
            with get_db_session() as session:
                forecast = generate_forecast_from_db(
                    session=session,
                    storm_identifier=storm_identifier,
                    agency=agency.upper(),
                    issue_time_utc=issue_time_utc,
                    horizons_hours=horizons_hours,
                )
                verification = verify_forecast_from_db(
                    session=session,
                    forecast=forecast,
                    tolerance_hours=3.0,
                )
        except Exception as db_err:
            # Fall back to offline demo cache
            clean_name = storm_identifier.upper()
            cache_track = None
            for p_file in (DEMO_CACHE_DIR / "storms").glob("*_track.json"):
                if clean_name in p_file.name.upper():
                    cache_track = p_file
                    break
            if cache_track and cache_track.is_file():
                with open(cache_track, encoding="utf-8") as f:
                    track_data = json.load(f)
                forecast_out = compute_baseline_cyclone_forecast(
                    storm_id=clean_name,
                    storm_name=clean_name,
                    observations=track_data,
                    issue_time_utc=issue_time_utc,
                    horizons_hours=horizons_hours,
                )
                res = forecast_out.model_dump()
                res["forecast_points"] = [
                    {
                        "lead_time_hours": hp.lead_time_hours,
                        "valid_time_utc": hp.valid_time_utc.isoformat()
                        if isinstance(hp.valid_time_utc, datetime)
                        else str(hp.valid_time_utc),
                        "predicted_latitude": hp.predicted_latitude,
                        "predicted_longitude": hp.predicted_longitude,
                        "predicted_wind_speed_knots": hp.predicted_wind_speed_knots,
                        "predicted_imd_category": hp.predicted_imd_category,
                        "uncertainty_radius_km": hp.uncertainty_radius_km,
                    }
                    for hp in forecast_out.forecast_points
                ]

                # Match retrospective ground truth for hindsight verification
                future_obs = []
                for p in track_data:
                    p_time_str = p.get("iso_time") or p.get("observation_time_utc")
                    if p_time_str:
                        try:
                            p_dt = datetime.fromisoformat(p_time_str.replace("Z", "+00:00"))
                            if p_dt.tzinfo is None:
                                p_dt = p_dt.replace(tzinfo=UTC)
                            if p_dt > issue_time_utc:
                                future_obs.append((p_dt, p))
                        except Exception:
                            pass

                verification_list = []
                for hp in forecast_out.forecast_points:
                    target_dt = (
                        hp.valid_time_utc
                        if isinstance(hp.valid_time_utc, datetime)
                        else datetime.fromisoformat(str(hp.valid_time_utc).replace("Z", "+00:00"))
                    )
                    if target_dt.tzinfo is None:
                        target_dt = target_dt.replace(tzinfo=UTC)
                    best_match = None
                    min_diff = float("inf")
                    for p_dt, p in future_obs:
                        diff_sec = abs((p_dt - target_dt).total_seconds())
                        if diff_sec <= 3 * 3600 and diff_sec < min_diff:
                            min_diff = diff_sec
                            best_match = p

                    v_entry: dict[str, Any] = {
                        "lead_time_hours": hp.lead_time_hours,
                        "valid_time_utc": target_dt.isoformat(),
                        "predicted_latitude": hp.predicted_latitude,
                        "predicted_longitude": hp.predicted_longitude,
                        "actual_latitude": best_match.get("latitude") if best_match else None,
                        "actual_longitude": best_match.get("longitude") if best_match else None,
                        "actual_category": best_match.get("imd_category") if best_match else None,
                        "actual_wind_kt": best_match.get("wind_speed_knots") if best_match else None,
                        "track_error_km": None,
                        "wind_error_kt": None,
                    }
                    if (
                        best_match
                        and best_match.get("latitude") is not None
                        and best_match.get("longitude") is not None
                    ):
                        lat1_r = math.radians(hp.predicted_latitude)
                        lat2_r = math.radians(best_match["latitude"])
                        dlat_r = math.radians(best_match["latitude"] - hp.predicted_latitude)
                        dlon_r = math.radians(best_match["longitude"] - hp.predicted_longitude)
                        a_h = (
                            math.sin(dlat_r / 2.0) ** 2
                            + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon_r / 2.0) ** 2
                        )
                        c_h = 2.0 * math.atan2(math.sqrt(a_h), math.sqrt(max(0.0, 1.0 - a_h)))
                        err_km = round(6371.0 * c_h, 1)
                        v_entry["track_error_km"] = err_km
                        act_wind = best_match.get("wind_speed_knots")
                        pred_wind = hp.predicted_wind_speed_knots
                        if act_wind is not None and pred_wind is not None:
                            v_entry["wind_error_kt"] = round(abs(pred_wind - act_wind), 1)

                    verification_list.append(v_entry)

                valid_errs = [
                    v["track_error_km"]
                    for v in verification_list
                    if v.get("track_error_km") is not None
                ]
                res["mean_track_error_km"] = (
                    round(sum(valid_errs) / len(valid_errs), 2) if valid_errs else None
                )
                res["verification"] = verification_list
                return res
            raise RuntimeError(f"Forecast engine error: {db_err}") from db_err

        # Build rich unified response supporting both Module B contract and UI tables
        res = forecast.model_dump()
        res["forecast_points"] = [
            {
                "lead_time_hours": hp.lead_time_hours,
                "valid_time_utc": hp.valid_time_utc.isoformat(),
                "predicted_latitude": hp.predicted_latitude,
                "predicted_longitude": hp.predicted_longitude,
                "predicted_wind_speed_knots": hp.predicted_wind_trend_knots
                if hp.predicted_wind_trend_knots is not None
                else hp.predicted_wind_persistence_knots,
                "predicted_imd_category": hp.predicted_imd_category_trend
                or hp.predicted_imd_category_persistence,
                "uncertainty_radius_km": hp.uncertainty_radius_km,
            }
            for hp in forecast.forecast_horizons
        ]

        if verification:
            res["verification"] = [
                {
                    "lead_time_hours": vh.lead_time_hours,
                    "valid_time_utc": vh.valid_time_utc.isoformat(),
                    "predicted_latitude": vh.predicted_latitude,
                    "predicted_longitude": vh.predicted_longitude,
                    "actual_latitude": vh.actual_latitude,
                    "actual_longitude": vh.actual_longitude,
                    "actual_category": vh.actual_category,
                    "actual_wind_kt": vh.actual_wind_kt,
                    "track_error_km": vh.geodesic_track_error_km,
                    "wind_error_kt": vh.trend_wind_error_kt
                    if vh.trend_wind_error_kt is not None
                    else vh.persistence_wind_error_kt,
                }
                for vh in verification.verification_horizons
            ]

        return res

    @staticmethod
    def verify_forecast(
        forecast: CycloneForecastOutput,
        tolerance_hours: float = 3.0,
    ) -> HindsightVerificationOutput:
        """Evaluate predicted horizons against retrospective ground-truth fixes (> issue_time_utc)."""
        with get_db_session() as session:
            return verify_forecast_from_db(
                session=session,
                forecast=forecast,
                tolerance_hours=tolerance_hours,
            )

