"""Schemas for multi-horizon track and intensity forecast generation and verification."""

from pydantic import BaseModel, Field

from vayumarg.module_b.contracts import CycloneForecastOutput


class ForecastRequest(BaseModel):
    """Input payload to request deterministic or hybrid cyclone forecasting."""

    storm_sid: str | None = Field(
        default=None,
        description="Canonical IBTrACS SID or storm name (e.g. 2023156N10067, BIPARJOY)",
    )
    canonical_sid: str | None = Field(
        default=None,
        description="Authoritative IBTrACS SID alias (e.g. 2023156N10067)",
    )
    storm_name: str | None = Field(
        default=None,
        description="Storm name alias (e.g. BIPARJOY, AMPHAN)",
    )
    issue_time_utc: str = Field(
        ...,
        description="ISO 8601 UTC forecast issue timestamp (LEAKAGE SHIELD: only observations <= issue_time_utc are queried)",
    )
    agency: str = Field(
        default="IMD",
        description="Wind reference agency: IMD (3-min sustained), JTWC (1-min sustained), or IBTRACS",
    )
    horizons_hours: list[int] = Field(
        default=[6, 12, 24],
        description="Forecast horizons in hours (+6h, +12h, +24h)",
    )


class VerificationRequest(BaseModel):
    """Input payload for retrospective hindsight verification against ground-truth fixes."""

    forecast: CycloneForecastOutput
    tolerance_hours: float = Field(
        default=3.0,
        ge=0.5,
        le=12.0,
        description="Verification matching tolerance in hours",
    )

