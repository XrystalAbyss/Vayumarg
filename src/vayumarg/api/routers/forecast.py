"""Deterministic geodesic trajectory extrapolation and hindsight verification routes."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from vayumarg.api.schemas.forecast import ForecastRequest, VerificationRequest
from vayumarg.module_b.contracts import HindsightVerificationOutput
from vayumarg.services.forecast_service import ForecastService

router = APIRouter(tags=["Forecasting & Verification"])


@router.post("/api/forecast/generate")
def generate_forecast(req: ForecastRequest) -> dict[str, Any]:
    """Generate deterministic Geodesic Constant-Velocity extrapolation forecast (+6h, +12h, +24h).

    GROUND TRUTH LEAKAGE SHIELD:
    Strictly queries observations with timestamp <= issue_time_utc.
    """
    storm_ident = (req.canonical_sid or req.storm_sid or req.storm_name or "").strip()
    if not storm_ident:
        raise HTTPException(
            status_code=400, detail="Either storm_sid, canonical_sid, or storm_name must be provided."
        )

    try:
        issue_dt = datetime.fromisoformat(req.issue_time_utc.replace("Z", "+00:00"))
        if issue_dt.tzinfo is None:
            issue_dt = issue_dt.replace(tzinfo=UTC)
    except ValueError as ve:
        raise HTTPException(
            status_code=400, detail=f"Invalid ISO UTC timestamp: {req.issue_time_utc}"
        ) from ve

    try:
        return ForecastService.generate_forecast(
            storm_identifier=storm_ident,
            issue_time_utc=issue_dt,
            agency=req.agency,
            horizons_hours=req.horizons_hours,
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Forecast engine error: {ex}") from ex


@router.get("/api/storms/{storm_identifier}/forecast")
def get_storm_forecast(
    storm_identifier: str,
    issue_time_utc: str = Query(..., description="ISO 8601 UTC forecast issue timestamp"),
    agency: str = Query("IMD", description="Wind reference agency: IMD or JTWC"),
) -> dict[str, Any]:
    """Generate forecast via GET query parameters for quick client inspection."""
    req = ForecastRequest(
        storm_name=storm_identifier,
        issue_time_utc=issue_time_utc,
        agency=agency,
    )
    return generate_forecast(req)


@router.post("/api/forecast/verify", response_model=HindsightVerificationOutput)
def verify_forecast(req: VerificationRequest) -> HindsightVerificationOutput:
    """Evaluate predicted horizons against retrospective ground-truth fixes (> issue_time_utc)."""
    try:
        return ForecastService.verify_forecast(
            forecast=req.forecast,
            tolerance_hours=req.tolerance_hours,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Verification engine error: {ex}") from ex


@router.get("/api/forecast/demo-cases")
@router.get("/api/demo/scenarios")
@router.get("/api/scenarios")
def list_demo_cases() -> list[dict[str, Any]]:
    """Return pre-configured historical demonstration scenarios (BIPARJOY, AMPHAN, DANA, REMAL)."""
    return ForecastService.list_demo_cases()

