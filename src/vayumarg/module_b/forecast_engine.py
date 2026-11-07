"""Module B Forecast Engine: Geodesic Constant-Velocity Extrapolation & Hindsight Verification.

Implements scientific cyclone track and future wind forecasting for the North Indian Ocean:
1. Strict Ground Truth Leakage Protection: inputs strictly <= issue_time_utc.
2. Geodesic Great-Circle Forward Extrapolation using spherical trigonometry.
3. Agency track preservation and explicit wind averaging periods.
4. Persistence baseline and bounded recent-trend intensity comparators.
5. Independent Hindsight Verification path against future ground-truth fixes (> issue_time_utc).
6. Strongly typed RFC 7946 GeoJSON and coordinate sequences for reliable mapping.
"""

import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.database.schema import Storm, StormAlias, TrackObservation
from vayumarg.module_b.contracts import (
    CycloneForecastOutput,
    ForecastHorizonPoint,
    ForecastStatus,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
    HindsightHorizonVerification,
    HindsightVerificationOutput,
    HistoricalObservationPoint,
    MotionVector,
    RecordType,
)

EARTH_RADIUS_KM = 6371.0


def classify_imd_category(wind_kt: float | None) -> str | None:
    """Classify sustained wind into official IMD cyclone categories."""
    if wind_kt is None or math.isnan(wind_kt):
        return None
    if wind_kt < 17.0:
        return "Low Pressure Area"
    elif wind_kt < 28.0:
        return "Depression (D)"
    elif wind_kt < 34.0:
        return "Deep Depression (DD)"
    elif wind_kt < 48.0:
        return "Cyclonic Storm (CS)"
    elif wind_kt < 64.0:
        return "Severe Cyclonic Storm (SCS)"
    elif wind_kt < 90.0:
        return "Very Severe Cyclonic Storm (VSCS)"
    elif wind_kt < 120.0:
        return "Extremely Severe Cyclonic Storm (ESCS)"
    else:
        return "Super Cyclonic Storm (SuCS)"


def normalize_longitude(lon: float) -> float:
    """Normalize longitude to [-180.0, 180.0] degrees."""
    return (lon + 540.0) % 360.0 - 180.0


def calculate_great_circle_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km, handling longitude wrap."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)

    # Angular difference in longitude normalized to [-pi, pi]
    delta_lambda = math.radians(lon2 - lon1)
    delta_lambda = (delta_lambda + math.pi) % (2.0 * math.pi) - math.pi

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_KM * c


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate initial compass bearing from (lat1, lon1) to (lat2, lon2) in degrees [0, 360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_lambda = math.radians(lon2 - lon1)
    delta_lambda = (delta_lambda + math.pi) % (2.0 * math.pi) - math.pi

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(y, x)
    return (math.degrees(bearing_rad) + 360.0) % 360.0


def extrapolate_geodesic(
    lat: float, lon: float, bearing_deg: float, distance_km: float
) -> tuple[float, float]:
    """Calculate destination coordinates along great-circle arc from start, bearing, and distance."""
    if distance_km < 1e-6:
        return round(lat, 4), round(normalize_longitude(lon), 4)

    delta = distance_km / EARTH_RADIUS_KM
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)

    sin_phi2 = math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    sin_phi2 = max(-1.0, min(1.0, sin_phi2))
    phi2 = math.asin(sin_phi2)

    y = math.sin(theta) * math.sin(delta) * math.cos(phi1)
    x = math.cos(delta) - math.sin(phi1) * math.sin(phi2)
    lambda2 = lambda1 + math.atan2(y, x)

    lat2 = math.degrees(phi2)
    lon2 = normalize_longitude(math.degrees(lambda2))
    return round(lat2, 4), round(lon2, 4)


def validate_and_clean_observations(
    observations: list[dict[str, Any] | TrackObservation],
    issue_time_utc: datetime,
) -> list[HistoricalObservationPoint]:
    """Sort, filter, and validate historical observations strictly <= issue_time_utc.

    Rejects:
    - Observations with timestamp > issue_time_utc (LEAKAGE PROTECTION)
    - Missing or nonfinite coordinates (lat not in [-90, 90], lon not in [-180, 180])
    - Duplicated fixes (same timestamp)
    """
    clean_points: list[HistoricalObservationPoint] = []
    seen_timestamps: set[datetime] = set()

    for item in observations:
        if isinstance(item, TrackObservation):
            obs_dt = item.observation_time_utc
            lat = item.latitude
            lon = item.longitude
            w_kt = item.wind_speed_knots
            p_hpa = item.central_pressure_hpa
            avg_per = item.averaging_period or "3-min"
            cat = item.imd_category
            rec_id = item.source_record_id
        else:
            obs_dt = item["observation_time_utc"]
            lat = item.get("latitude")
            lon = item.get("longitude")
            w_kt = item.get("wind_speed_knots")
            p_hpa = item.get("central_pressure_hpa")
            avg_per = item.get("averaging_period", "3-min")
            cat = item.get("imd_category")
            rec_id = item.get("source_record_id")

        if obs_dt.tzinfo is None:
            obs_dt = obs_dt.replace(tzinfo=UTC)

        # STRICT GROUND TRUTH LEAKAGE SHIELD
        if obs_dt > issue_time_utc:
            continue

        # Coordinate sanity validation
        if lat is None or lon is None:
            continue
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            continue

        if math.isnan(lat_f) or math.isinf(lat_f) or math.isnan(lon_f) or math.isinf(lon_f):
            continue
        if not (-90.0 <= lat_f <= 90.0):
            continue
        lon_f = normalize_longitude(lon_f)

        # Wind speed sanity
        w_val: float | None = None
        if w_kt is not None:
            try:
                w_candidate = float(w_kt)
                if not math.isnan(w_candidate) and 0.0 <= w_candidate <= 300.0:
                    w_val = w_candidate
            except (ValueError, TypeError):
                w_val = None

        # Pressure sanity
        p_val: float | None = None
        if p_hpa is not None:
            try:
                p_candidate = float(p_hpa)
                if not math.isnan(p_candidate) and 800.0 <= p_candidate <= 1080.0:
                    p_val = p_candidate
            except (ValueError, TypeError):
                p_val = None

        category = cat or classify_imd_category(w_val)

        pt = HistoricalObservationPoint(
            observation_time_utc=obs_dt,
            latitude=round(lat_f, 4),
            longitude=round(lon_f, 4),
            wind_speed_knots=w_val,
            central_pressure_hpa=p_val,
            averaging_period=avg_per,
            imd_category=category,
            source_record_id=str(rec_id) if rec_id is not None else None,
            record_type=RecordType.HISTORICAL_INPUT,
        )
        clean_points.append(pt)

    # Sort strictly chronologically
    clean_points.sort(key=lambda p: p.observation_time_utc)

    # Deduplicate timestamps (retain the first chronologically validated fix)
    deduped: list[HistoricalObservationPoint] = []
    for pt in clean_points:
        if pt.observation_time_utc not in seen_timestamps:
            seen_timestamps.add(pt.observation_time_utc)
            deduped.append(pt)

    return deduped


def build_forecast_geojson(
    history: list[HistoricalObservationPoint],
    horizons: list[ForecastHorizonPoint],
) -> GeoJsonFeatureCollection:
    """Build standard RFC 7946 GeoJSON FeatureCollection for frontend visualization.

    GeoJSON standard uses [longitude, latitude] coordinate ordering.
    """
    features: list[GeoJsonFeature] = []

    # 1. Historical track points
    hist_coords = []
    for p in history:
        lon, lat = p.longitude, p.latitude
        hist_coords.append([lon, lat])
        features.append(
            GeoJsonFeature(
                geometry={"type": "Point", "coordinates": [lon, lat]},
                properties={
                    "stage": "HISTORICAL_INPUT",
                    "observation_time_utc": p.observation_time_utc.isoformat(),
                    "latitude": lat,
                    "longitude": lon,
                    "wind_speed_knots": p.wind_speed_knots,
                    "central_pressure_hpa": p.central_pressure_hpa,
                    "imd_category": p.imd_category,
                    "averaging_period": p.averaging_period,
                },
            )
        )

    # Historical LineString
    if len(hist_coords) >= 2:
        features.append(
            GeoJsonFeature(
                geometry={"type": "LineString", "coordinates": hist_coords},
                properties={"stage": "HISTORICAL_TRACK_LINE", "point_count": len(hist_coords)},
            )
        )

    # 2. Forecast points and trajectory LineString
    if history and horizons:
        curr = history[-1]
        fc_coords = [[curr.longitude, curr.latitude]]

        for hp in horizons:
            lon, lat = hp.predicted_longitude, hp.predicted_latitude
            fc_coords.append([lon, lat])
            features.append(
                GeoJsonFeature(
                    geometry={"type": "Point", "coordinates": [lon, lat]},
                    properties={
                        "stage": "BASELINE_FORECAST",
                        "lead_time_hours": hp.lead_time_hours,
                        "valid_time_utc": hp.valid_time_utc.isoformat(),
                        "predicted_latitude": lat,
                        "predicted_longitude": lon,
                        "projected_distance_km": hp.projected_distance_km,
                        "predicted_wind_persistence_knots": hp.predicted_wind_persistence_knots,
                        "predicted_wind_trend_knots": hp.predicted_wind_trend_knots,
                        "predicted_imd_category_persistence": hp.predicted_imd_category_persistence,
                        "predicted_imd_category_trend": hp.predicted_imd_category_trend,
                        "uncertainty_radius_km": hp.uncertainty_radius_km,
                    },
                )
            )

        if len(fc_coords) >= 2:
            features.append(
                GeoJsonFeature(
                    geometry={"type": "LineString", "coordinates": fc_coords},
                    properties={
                        "stage": "FORECAST_TRAJECTORY_LINE",
                        "horizons": [h.lead_time_hours for h in horizons],
                    },
                )
            )

    return GeoJsonFeatureCollection(features=features)


def compute_geodesic_forecast(
    storm_id: str,
    storm_sid: str,
    storm_name: str,
    season_year: int,
    primary_basin: str,
    source_agency: str,
    observations: list[dict[str, Any] | TrackObservation],
    issue_time_utc: datetime,
    horizons_hours: list[int] | None = None,
    max_fix_recency_hours: float = 24.0,
) -> CycloneForecastOutput:
    """Core mathematical forecast calculation strictly isolated from future observations.

    Guarantees:
    - 0 observations > issue_time_utc are ever read or calculated.
    - Handles zero displacement, irregular intervals, longitude wrap.
    - Employs geodesic forward projection equations.
    - Returns UNAVAILABLE if last fixes are insufficient or too distant.
    """
    if horizons_hours is None:
        horizons_hours = [6, 12, 24]
    horizons_hours = sorted(set(horizons_hours))

    if issue_time_utc.tzinfo is None:
        issue_time_utc = issue_time_utc.replace(tzinfo=UTC)

    # 1. Clean and validate historical observations
    history = validate_and_clean_observations(observations, issue_time_utc)

    # 2. Check sufficient history
    if len(history) < 2:
        return CycloneForecastOutput(
            status=ForecastStatus.UNAVAILABLE,
            unavailability_reason=(
                f"Insufficient historical track points prior to {issue_time_utc.isoformat()}. "
                f"Required at least 2 usable fixes, found {len(history)}."
            ),
            storm_id=storm_id,
            storm_sid=storm_sid,
            storm_name=storm_name,
            season_year=season_year,
            primary_basin=primary_basin,
            source_agency=source_agency,
            wind_averaging_period="3-min" if source_agency == "IMD" else "1-min",
            issue_time_utc=issue_time_utc,
            input_observation_count=len(history),
            historical_track_used=history,
            forecast_horizons=[],
        )

    # 3. Check recency of latest fix
    curr_fix = history[-1]
    prev_fix = history[-2]

    time_since_last_fix = (issue_time_utc - curr_fix.observation_time_utc).total_seconds() / 3600.0
    if time_since_last_fix > max_fix_recency_hours:
        return CycloneForecastOutput(
            status=ForecastStatus.UNAVAILABLE,
            unavailability_reason=(
                f"Latest usable track fix at {curr_fix.observation_time_utc.isoformat()} is "
                f"{time_since_last_fix:.1f} hours prior to issue time {issue_time_utc.isoformat()}, "
                f"exceeding operational recency threshold of {max_fix_recency_hours:.0f} hours."
            ),
            storm_id=storm_id,
            storm_sid=storm_sid,
            storm_name=storm_name,
            season_year=season_year,
            primary_basin=primary_basin,
            source_agency=source_agency,
            wind_averaging_period=curr_fix.averaging_period,
            issue_time_utc=issue_time_utc,
            input_observation_count=len(history),
            historical_track_used=history,
            forecast_horizons=[],
        )

    # 4. Calculate elapsed time and velocity
    delta_hours = (
        curr_fix.observation_time_utc - prev_fix.observation_time_utc
    ).total_seconds() / 3600.0
    if delta_hours <= 0.0:
        return CycloneForecastOutput(
            status=ForecastStatus.UNAVAILABLE,
            unavailability_reason=f"Non-positive elapsed time interval ({delta_hours:.2f}h) between last fixes.",
            storm_id=storm_id,
            storm_sid=storm_sid,
            storm_name=storm_name,
            season_year=season_year,
            primary_basin=primary_basin,
            source_agency=source_agency,
            wind_averaging_period=curr_fix.averaging_period,
            issue_time_utc=issue_time_utc,
            input_observation_count=len(history),
            historical_track_used=history,
            forecast_horizons=[],
        )

    displacement_km = calculate_great_circle_distance_km(
        prev_fix.latitude, prev_fix.longitude, curr_fix.latitude, curr_fix.longitude
    )

    if displacement_km < 1e-4:
        # Zero displacement: stationary system
        speed_kmh = 0.0
        bearing_deg = 0.0
    else:
        speed_kmh = displacement_km / delta_hours
        bearing_deg = calculate_bearing_deg(
            prev_fix.latitude, prev_fix.longitude, curr_fix.latitude, curr_fix.longitude
        )

    motion_vector = MotionVector(
        speed_kmh=round(speed_kmh, 2),
        bearing_deg=round(bearing_deg, 2),
        displacement_km=round(displacement_km, 2),
        delta_hours=round(delta_hours, 2),
        source_fix_prev_utc=prev_fix.observation_time_utc,
        source_fix_curr_utc=curr_fix.observation_time_utc,
    )

    # 5. Wind baseline: Persistence + Bounded recent trend
    curr_wind = curr_fix.wind_speed_knots
    prev_wind = prev_fix.wind_speed_knots

    bounded_trend_per_hour: float | None = None
    if curr_wind is not None and prev_wind is not None and delta_hours > 0.0:
        raw_trend = (curr_wind - prev_wind) / delta_hours
        bounded_trend_per_hour = max(-5.0, min(5.0, raw_trend))

    # 6. Extrapolate forward for requested horizons
    forecast_points: list[ForecastHorizonPoint] = []
    # Uncertainty radii roughly calibrated to North Indian Ocean operational track errors
    uncertainty_map = {6: 50.0, 12: 85.0, 24: 140.0}

    for h in horizons_hours:
        valid_dt = issue_time_utc + timedelta(hours=h)
        proj_dist_km = speed_kmh * h

        if proj_dist_km < 1e-4:
            pred_lat, pred_lon = curr_fix.latitude, curr_fix.longitude
        else:
            pred_lat, pred_lon = extrapolate_geodesic(
                curr_fix.latitude, curr_fix.longitude, bearing_deg, proj_dist_km
            )

        # Persistence wind
        wind_persist = curr_wind
        cat_persist = classify_imd_category(wind_persist)

        # Bounded trend wind comparator
        wind_trend: float | None = None
        cat_trend: str | None = None
        if curr_wind is not None and bounded_trend_per_hour is not None:
            # Trend dampening as horizon expands: 100% at 0h down to 33% at 24h
            damping = max(0.0, 1.0 - (h / 36.0))
            projected_w = curr_wind + (bounded_trend_per_hour * h * damping)
            wind_trend = round(max(15.0, min(185.0, projected_w)), 1)
            cat_trend = classify_imd_category(wind_trend)

        uncert_km = uncertainty_map.get(h, 40.0 + (h * 4.5))

        f_point = ForecastHorizonPoint(
            lead_time_hours=h,
            valid_time_utc=valid_dt,
            predicted_latitude=pred_lat,
            predicted_longitude=pred_lon,
            projected_distance_km=round(proj_dist_km, 2),
            predicted_wind_persistence_knots=round(wind_persist, 1)
            if wind_persist is not None
            else None,
            predicted_wind_trend_knots=wind_trend,
            predicted_imd_category_persistence=cat_persist,
            predicted_imd_category_trend=cat_trend,
            uncertainty_radius_km=round(uncert_km, 1),
            record_type=RecordType.BASELINE_FORECAST,
        )
        forecast_points.append(f_point)

    geojson_doc = build_forecast_geojson(history, forecast_points)

    return CycloneForecastOutput(
        status=ForecastStatus.SUCCESS,
        storm_id=storm_id,
        storm_sid=storm_sid,
        storm_name=storm_name,
        season_year=season_year,
        primary_basin=primary_basin,
        source_agency=source_agency,
        wind_averaging_period=curr_fix.averaging_period,
        issue_time_utc=issue_time_utc,
        input_observation_count=len(history),
        current_position=curr_fix,
        translational_motion=motion_vector,
        forecast_horizons=forecast_points,
        historical_track_used=history,
        geojson=geojson_doc,
    )


def compute_hindsight_verification(
    forecast: CycloneForecastOutput,
    future_observations: list[dict[str, Any] | TrackObservation],
    tolerance_hours: float = 3.0,
) -> HindsightVerificationOutput:
    """Evaluate predicted track and intensity against actual retrospective ground truth.

    Guarantees:
    - Operates ONLY post-facto.
    - Never modifies forecast values.
    - Tolerates missing target fixes without fabricating actual positions.
    """
    clean_future: list[HistoricalObservationPoint] = []
    issue_t = forecast.issue_time_utc

    for item in future_observations:
        if isinstance(item, TrackObservation):
            obs_dt = item.observation_time_utc
            lat = item.latitude
            lon = item.longitude
            w_kt = item.wind_speed_knots
            cat = item.imd_category
        else:
            obs_dt = item["observation_time_utc"]
            lat = item.get("latitude")
            lon = item.get("longitude")
            w_kt = item.get("wind_speed_knots")
            cat = item.get("imd_category")

        if obs_dt.tzinfo is None:
            obs_dt = obs_dt.replace(tzinfo=UTC)

        # STRICTLY FUTURE OBS ONLY
        if obs_dt <= issue_t:
            continue
        if lat is None or lon is None:
            continue
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            continue
        if math.isnan(lat_f) or math.isnan(lon_f):
            continue

        clean_future.append(
            HistoricalObservationPoint(
                observation_time_utc=obs_dt,
                latitude=round(lat_f, 4),
                longitude=round(normalize_longitude(lon_f), 4),
                wind_speed_knots=float(w_kt)
                if w_kt is not None and not math.isnan(float(w_kt))
                else None,
                imd_category=cat
                or classify_imd_category(float(w_kt) if w_kt is not None else None),
                record_type=RecordType.FUTURE_OBSERVATION_FOR_VERIFICATION,
            )
        )

    clean_future.sort(key=lambda p: p.observation_time_utc)

    verifications: list[HindsightHorizonVerification] = []
    track_errors: list[float] = []
    wind_errors_persist: list[float] = []
    wind_errors_trend: list[float] = []
    matched_count = 0

    for hp in forecast.forecast_horizons:
        target_time = hp.valid_time_utc
        # Find nearest future observation within tolerance
        best_match: HistoricalObservationPoint | None = None
        best_diff_sec = tolerance_hours * 3600.0 + 1e-3

        for candidate in clean_future:
            diff_sec = abs((candidate.observation_time_utc - target_time).total_seconds())
            if diff_sec <= (tolerance_hours * 3600.0) and diff_sec < best_diff_sec:
                best_diff_sec = diff_sec
                best_match = candidate

        if best_match is not None:
            matched_count += 1
            err_km = calculate_great_circle_distance_km(
                hp.predicted_latitude,
                hp.predicted_longitude,
                best_match.latitude,
                best_match.longitude,
            )
            track_errors.append(err_km)

            # Wind errors
            w_err_persist: float | None = None
            if (
                hp.predicted_wind_persistence_knots is not None
                and best_match.wind_speed_knots is not None
            ):
                w_err_persist = round(
                    abs(hp.predicted_wind_persistence_knots - best_match.wind_speed_knots), 1
                )
                wind_errors_persist.append(w_err_persist)

            w_err_trend: float | None = None
            if (
                hp.predicted_wind_trend_knots is not None
                and best_match.wind_speed_knots is not None
            ):
                w_err_trend = round(
                    abs(hp.predicted_wind_trend_knots - best_match.wind_speed_knots), 1
                )
                wind_errors_trend.append(w_err_trend)

            verifications.append(
                HindsightHorizonVerification(
                    lead_time_hours=hp.lead_time_hours,
                    valid_time_utc=hp.valid_time_utc,
                    target_status="VERIFIED",
                    predicted_latitude=hp.predicted_latitude,
                    predicted_longitude=hp.predicted_longitude,
                    actual_observation_time_utc=best_match.observation_time_utc,
                    actual_latitude=best_match.latitude,
                    actual_longitude=best_match.longitude,
                    geodesic_track_error_km=round(err_km, 2),
                    predicted_wind_persistence_kt=hp.predicted_wind_persistence_knots,
                    predicted_wind_trend_kt=hp.predicted_wind_trend_knots,
                    actual_wind_kt=best_match.wind_speed_knots,
                    persistence_wind_error_kt=w_err_persist,
                    trend_wind_error_kt=w_err_trend,
                    actual_category=best_match.imd_category,
                    record_type=RecordType.FUTURE_OBSERVATION_FOR_VERIFICATION,
                    notes=f"Matched retrospective observation at {best_match.observation_time_utc.isoformat()} (Δt={best_diff_sec / 3600.0:.2f}h).",
                )
            )
        else:
            verifications.append(
                HindsightHorizonVerification(
                    lead_time_hours=hp.lead_time_hours,
                    valid_time_utc=hp.valid_time_utc,
                    target_status="TARGET_UNAVAILABLE",
                    predicted_latitude=hp.predicted_latitude,
                    predicted_longitude=hp.predicted_longitude,
                    predicted_wind_persistence_kt=hp.predicted_wind_persistence_knots,
                    predicted_wind_trend_kt=hp.predicted_wind_trend_knots,
                    record_type=RecordType.FUTURE_OBSERVATION_FOR_VERIFICATION,
                    notes=f"No retrospective track observation available within ±{tolerance_hours:.1f}h of valid time.",
                )
            )

    mean_err_km = round(sum(track_errors) / len(track_errors), 2) if track_errors else None
    mean_w_persist = (
        round(sum(wind_errors_persist) / len(wind_errors_persist), 2)
        if wind_errors_persist
        else None
    )
    mean_w_trend = (
        round(sum(wind_errors_trend) / len(wind_errors_trend), 2) if wind_errors_trend else None
    )

    # Verification GeoJSON with actual matched points
    features: list[GeoJsonFeature] = []
    for v in verifications:
        if v.actual_latitude is not None and v.actual_longitude is not None:
            features.append(
                GeoJsonFeature(
                    geometry={
                        "type": "Point",
                        "coordinates": [v.actual_longitude, v.actual_latitude],
                    },
                    properties={
                        "stage": "FUTURE_OBSERVATION_FOR_VERIFICATION",
                        "lead_time_hours": v.lead_time_hours,
                        "valid_time_utc": v.valid_time_utc.isoformat(),
                        "actual_observation_time_utc": v.actual_observation_time_utc.isoformat()
                        if v.actual_observation_time_utc
                        else None,
                        "actual_latitude": v.actual_latitude,
                        "actual_longitude": v.actual_longitude,
                        "geodesic_track_error_km": v.geodesic_track_error_km,
                        "actual_wind_kt": v.actual_wind_kt,
                        "persistence_wind_error_kt": v.persistence_wind_error_kt,
                    },
                )
            )

    return HindsightVerificationOutput(
        storm_id=forecast.storm_id,
        storm_sid=forecast.storm_sid,
        storm_name=forecast.storm_name,
        source_agency=forecast.source_agency,
        issue_time_utc=forecast.issue_time_utc,
        verification_tolerance_hours=tolerance_hours,
        horizons_evaluated=len(forecast.forecast_horizons),
        horizons_matched=matched_count,
        mean_track_error_km=mean_err_km,
        mean_wind_error_persistence_kt=mean_w_persist,
        mean_wind_error_trend_kt=mean_w_trend,
        verification_horizons=verifications,
        geojson=GeoJsonFeatureCollection(features=features) if features else None,
    )


def resolve_storm_in_database(
    session: Session,
    storm_identifier: str,
) -> tuple[Storm, str]:
    """Resolve storm in database by IBTrACS SID, UUID, or canonical name.

    Returns (Storm entity, canonical_sid string).
    Raises ValueError if not found.
    """
    ident = storm_identifier.strip()

    # 1. Try canonical SID lookup via StormAlias (e.g. 2023156N10067)
    alias = session.execute(
        select(StormAlias).where(
            StormAlias.source_agency == "IBTRACS",
            StormAlias.agency_storm_id == ident,
        )
    ).scalar_one_or_none()

    if alias:
        storm = session.execute(
            select(Storm).where(Storm.id == alias.storm_id)
        ).scalar_one_or_none()
        if storm:
            return storm, alias.agency_storm_id

    # 2. Try UUID lookup
    try:
        val_uuid = uuid.UUID(ident)
        storm = session.execute(select(Storm).where(Storm.id == val_uuid)).scalar_one_or_none()
        if storm:
            ibtracs_alias = session.execute(
                select(StormAlias.agency_storm_id).where(
                    StormAlias.storm_id == storm.id,
                    StormAlias.source_agency == "IBTRACS",
                )
            ).scalar_one_or_none()
            return storm, ibtracs_alias or str(storm.id)
    except (ValueError, AttributeError):
        pass

    # 3. Try canonical name lookup (case-insensitive)
    storm = (
        session.execute(
            select(Storm)
            .where(Storm.canonical_name.ilike(ident))
            .order_by(Storm.season_year.desc())
        )
        .scalars()
        .first()
    )

    if storm:
        ibtracs_alias = session.execute(
            select(StormAlias.agency_storm_id).where(
                StormAlias.storm_id == storm.id,
                StormAlias.source_agency == "IBTRACS",
            )
        ).scalar_one_or_none()
        return storm, ibtracs_alias or str(storm.id)

    raise ValueError(f"Cyclone not found in database for identifier: '{storm_identifier}'")


def generate_forecast_from_db(
    session: Session,
    storm_identifier: str,
    agency: str,
    issue_time_utc: datetime,
    horizons_hours: list[int] | None = None,
) -> CycloneForecastOutput:
    """Generate forecast querying solely historical observations <= issue_time_utc from PostgreSQL."""
    storm, sid = resolve_storm_in_database(session, storm_identifier)

    if issue_time_utc.tzinfo is None:
        issue_time_utc = issue_time_utc.replace(tzinfo=UTC)

    # STRICT DATABASE LEAKAGE PREVENTION QUERY: <= issue_time_utc
    stmt = (
        select(TrackObservation)
        .where(
            TrackObservation.storm_id == storm.id,
            TrackObservation.source_agency == agency,
            TrackObservation.observation_time_utc <= issue_time_utc,
        )
        .order_by(TrackObservation.observation_time_utc)
    )
    history_obs = session.execute(stmt).scalars().all()

    return compute_geodesic_forecast(
        storm_id=str(storm.id),
        storm_sid=sid,
        storm_name=storm.canonical_name,
        season_year=storm.season_year,
        primary_basin=storm.primary_basin,
        source_agency=agency,
        observations=list(history_obs),
        issue_time_utc=issue_time_utc,
        horizons_hours=horizons_hours,
    )


def verify_forecast_from_db(
    session: Session,
    forecast: CycloneForecastOutput,
    tolerance_hours: float = 3.0,
) -> HindsightVerificationOutput:
    """Evaluate hindsight verification querying only future observations > issue_time_utc from PostgreSQL."""
    val_uuid = uuid.UUID(forecast.storm_id)

    stmt = (
        select(TrackObservation)
        .where(
            TrackObservation.storm_id == val_uuid,
            TrackObservation.source_agency == forecast.source_agency,
            TrackObservation.observation_time_utc > forecast.issue_time_utc,
        )
        .order_by(TrackObservation.observation_time_utc)
    )
    future_obs = session.execute(stmt).scalars().all()

    return compute_hindsight_verification(
        forecast=forecast,
        future_observations=list(future_obs),
        tolerance_hours=tolerance_hours,
    )
