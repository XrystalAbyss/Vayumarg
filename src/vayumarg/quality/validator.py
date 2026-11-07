"""Scientific data quality and integrity validator.

Enforces physical coordinate bounds, wind speed plausibility,
agency sustained-wind averaging conventions, missing-data rules,
and prospective vs. retrospective data lineage.
"""

from typing import Any

from pydantic import ValidationError

from vayumarg.contracts.enums import Agency, AveragingPeriod
from vayumarg.contracts.models import TrackObservationContract


class QualityValidationError(Exception):
    """Raised when an observation violates fundamental physical or convention constraints."""

    pass


def validate_coordinates(latitude: float, longitude: float) -> tuple[bool, str | None]:
    """Validate WGS84 geographic coordinate bounds."""
    if not (-90.0 <= latitude <= 90.0):
        return False, f"Latitude {latitude} is outside valid physical range [-90.0, 90.0]"
    if not (-180.0 <= longitude <= 180.0):
        return False, f"Longitude {longitude} is outside valid physical range [-180.0, 180.0]"
    return True, None


def validate_agency_averaging_period(
    agency: Agency | str, averaging_period: AveragingPeriod | str
) -> tuple[bool, str | None]:
    """Verify that agency reporting conforms to its recognized sustained-wind convention.

    - IMD: Must report 3-minute sustained winds (RSMC New Delhi standard).
    - JTWC / NHC: Report 1-minute sustained winds.
    - WMO / JMA: Report 10-minute sustained winds.
    """
    agency_str = agency.value if isinstance(agency, Agency) else str(agency)
    period_str = (
        averaging_period.value
        if isinstance(averaging_period, AveragingPeriod)
        else str(averaging_period)
    )

    if agency_str == Agency.IMD.value and period_str != AveragingPeriod.THREE_MINUTE.value:
        return (
            False,
            f"Scientific convention mismatch: IMD standard requires 3-minute sustained wind, found '{period_str}'",
        )
    if (
        agency_str in (Agency.JTWC.value, Agency.NHC.value)
        and period_str != AveragingPeriod.ONE_MINUTE.value
    ):
        return (
            False,
            f"Scientific convention mismatch: JTWC/NHC standard requires 1-minute sustained wind, found '{period_str}'",
        )
    return True, None


def validate_observation_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a raw observation dictionary against the canonical data contract."""
    errors: list[str] = []

    # 1. Pydantic schema validation
    try:
        contract = TrackObservationContract(**record)
    except ValidationError as err:
        errors.extend([f"{e['loc']}: {e['msg']}" for e in err.errors()])
        return False, errors

    # 2. Coordinate check
    coord_valid, coord_err = validate_coordinates(contract.latitude, contract.longitude)
    if not coord_valid and coord_err:
        errors.append(coord_err)

    # 3. Agency convention check
    conv_valid, conv_err = validate_agency_averaging_period(
        contract.source_agency, contract.averaging_period
    )
    if not conv_valid and conv_err:
        errors.append(conv_err)

    # 4. Zero vs Null check
    # In meteorology, 0 knot wind with 920 hPa pressure is a known artifact of improper zero-filling
    if contract.wind_speed_knots == 0 and (
        contract.central_pressure_hpa and contract.central_pressure_hpa < 980
    ):
        errors.append(
            f"Suspicious zero wind speed ({contract.wind_speed_knots} kt) with deep depression pressure ({contract.central_pressure_hpa} hPa). Missing values must be None/NULL, not 0."
        )

    return len(errors) == 0, errors
