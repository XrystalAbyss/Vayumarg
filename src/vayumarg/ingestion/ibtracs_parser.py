"""Deterministic parser for NOAA IBTrACS North Indian Ocean CSV files.

Parses raw IBTrACS v04r01 rows, preserving:
1. Two-header offset (Row 1: column headers, Row 2: column units).
2. Authoritative storm identity (SID, Season, Basin, Name, Nature).
3. Multi-agency observations (WMO consensus, IMD/NEWDELHI, JTWC/USA).
4. Strict unit separation (10-min, 3-min, 1-min sustained winds).
5. Exact NULL preservation without artificial zero-coercion.
"""

import csv
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from geoalchemy2.elements import WKTElement

from vayumarg.contracts.enums import Agency, AveragingPeriod
from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.ingestion.ibtracs_parser")


def parse_clean_float(val: str | None) -> float | None:
    """Parse string to float or return None if empty/whitespace."""
    if val is None:
        return None
    s = val.strip()
    if not s or s in ("-999", "-999.0", "NaN", "null", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_clean_str(val: str | None) -> str | None:
    """Parse string or return None if empty/whitespace."""
    if val is None:
        return None
    s = val.strip()
    return s if s else None


class IBTrACSParser:
    """Parses NOAA IBTrACS CSV into domain-ready storm and observation payloads."""

    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.is_file():
            raise FileNotFoundError(f"IBTrACS file not found: {self.file_path}")

    @staticmethod
    def resolve_wmo_averaging(wmo_agency: str | None, wmo_wind: float | None) -> str:
        """Resolve authoritative sustained wind averaging period based on WMO_AGENCY provenance."""
        if wmo_wind is None:
            return AveragingPeriod.UNKNOWN.value
        if not wmo_agency:
            return AveragingPeriod.UNKNOWN.value
        agency_norm = wmo_agency.strip().lower()
        if agency_norm == "newdelhi":
            return AveragingPeriod.THREE_MINUTE.value
        elif agency_norm == "tokyo":
            return AveragingPeriod.TEN_MINUTE.value
        elif agency_norm in ("hurdat_atl", "atcf"):
            return AveragingPeriod.ONE_MINUTE.value
        return AveragingPeriod.UNKNOWN.value

    _resolve_wmo_averaging = resolve_wmo_averaging

    def iter_records(
        self,
        sid_filter: set[str] | None = None,
        max_rows: int | None = None,
    ) -> Generator[tuple[dict[str, Any], list[dict[str, Any]]], None, None]:
        """Iterate through the IBTrACS CSV, yielding (storm_dict, observations_list) per row.

        Args:
            sid_filter: Optional set of SIDs to restrict parsing to (e.g. pilot storms).
            max_rows: Optional limit on the number of raw rows processed.

        Yields:
            Tuple of:
            - storm_info: dictionary containing storm metadata and alias attributes.
            - observations: list of observation dictionaries (WMO, IMD, JTWC where present).
        """
        with open(self.file_path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)

            # Row 1: Headers
            try:
                headers = next(reader)
            except StopIteration:
                return

            # Row 2: Units
            try:
                _units = next(reader)
            except StopIteration:
                return

            header_map = {col.strip(): idx for idx, col in enumerate(headers)}

            # Validate mandatory columns
            mandatory = ["SID", "SEASON", "BASIN", "NAME", "ISO_TIME", "LAT", "LON"]
            for m in mandatory:
                if m not in header_map:
                    raise ValueError(f"IBTrACS file missing mandatory column '{m}'")

            processed_rows = 0
            for line_idx, row in enumerate(reader, start=3):
                if max_rows is not None and processed_rows >= max_rows:
                    break

                if not row or len(row) < len(headers):
                    continue

                def get_val(col_name: str, curr_row: list[str] = row) -> str:
                    idx = header_map.get(col_name)
                    return curr_row[idx].strip() if idx is not None and idx < len(curr_row) else ""

                sid = get_val("SID")
                if not sid:
                    continue

                if sid_filter and sid not in sid_filter:
                    continue

                season_raw = get_val("SEASON")
                try:
                    season = int(season_raw)
                except ValueError:
                    season = 0

                raw_name = get_val("NAME")
                canonical_name = raw_name if raw_name and raw_name != "NOT_NAMED" else "UNNAMED"
                basin = get_val("BASIN") or "NI"
                subbasin = get_val("SUBBASIN") or None
                nature = get_val("NATURE") or "TS"
                usa_atcf_id = parse_clean_str(get_val("USA_ATCF_ID"))

                storm_info = {
                    "sid": sid,
                    "canonical_name": canonical_name,
                    "raw_name": raw_name,
                    "season_year": season,
                    "primary_basin": basin,
                    "subbasin": subbasin,
                    "nature": nature,
                    "usa_atcf_id": usa_atcf_id,
                }

                # Parse temporal convention
                iso_time_str = get_val("ISO_TIME")
                try:
                    obs_time_utc = datetime.strptime(iso_time_str, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=UTC
                    )
                except ValueError:
                    logger.warning(
                        "Line %d: Skipping unparseable ISO_TIME '%s'", line_idx, iso_time_str
                    )
                    continue

                # Main track position
                main_lat = parse_clean_float(get_val("LAT"))
                main_lon = parse_clean_float(get_val("LON"))

                if main_lat is None or main_lon is None:
                    continue

                observations: list[dict[str, Any]] = []

                # 1. Official IBTrACS / WMO Consensus Observation
                wmo_wind = parse_clean_float(get_val("WMO_WIND"))
                wmo_pres = parse_clean_float(get_val("WMO_PRES"))
                wmo_agency = parse_clean_str(get_val("WMO_AGENCY"))
                track_type = parse_clean_str(get_val("TRACK_TYPE")) or "main"

                # Check bounds
                if wmo_wind is not None and not (0.0 <= wmo_wind <= 300.0):
                    wmo_wind = None
                if wmo_pres is not None and not (800.0 <= wmo_pres <= 1080.0):
                    wmo_pres = None

                # Correct scientific sustained wind averaging period based on WMO_AGENCY
                wmo_avg = self.resolve_wmo_averaging(wmo_agency, wmo_wind)

                is_cross_basin = (
                    (basin != "NI") or (main_lat > 40.0) or (main_lon < 30.0 or main_lon > 105.0)
                )
                obs_quality = "CROSS_BASIN" if is_cross_basin else "VALID"

                observations.append(
                    {
                        "source_agency": Agency.IBTRACS.value,
                        "wmo_agency": wmo_agency,
                        "source_record_id": f"ROW_{line_idx}:IBTRACS",
                        "observation_time_utc": obs_time_utc,
                        "latitude": main_lat,
                        "longitude": main_lon,
                        "geom": WKTElement(f"POINT({main_lon} {main_lat})", srid=4326),
                        "wind_speed_knots": wmo_wind,
                        "original_wind_speed": wmo_wind,
                        "original_wind_unit": "kts",
                        "averaging_period": wmo_avg,
                        "central_pressure_hpa": wmo_pres,
                        "pressure_drop_hpa": None,
                        "imd_category": None,
                        "is_retrospective_best_track": True,
                        "quality_flag": obs_quality,
                        "raw_payload": {
                            "sid": sid,
                            "wmo_agency": wmo_agency,
                            "is_selected_agency_wind": bool(wmo_agency),
                            "selected_agency": wmo_agency,
                            "track_type": track_type,
                            "dist2land": parse_clean_float(get_val("DIST2LAND")),
                            "landfall": parse_clean_float(get_val("LANDFALL")),
                            "iflag": parse_clean_str(get_val("IFLAG")),
                        },
                    }
                )

                # 2. IMD / RSMC New Delhi Observation
                imd_wind_raw = get_val("NEWDELHI_WIND")
                imd_pres_raw = get_val("NEWDELHI_PRES")
                imd_grade = parse_clean_str(get_val("NEWDELHI_GRADE"))
                imd_lat_raw = get_val("NEWDELHI_LAT")
                imd_lon_raw = get_val("NEWDELHI_LON")

                has_imd = any([imd_wind_raw, imd_pres_raw, imd_grade, imd_lat_raw, imd_lon_raw])
                if has_imd:
                    imd_lat = parse_clean_float(imd_lat_raw) or main_lat
                    imd_lon = parse_clean_float(imd_lon_raw) or main_lon
                    imd_wind = parse_clean_float(imd_wind_raw)
                    imd_pres = parse_clean_float(imd_pres_raw)
                    imd_dp = parse_clean_float(get_val("NEWDELHI_DP"))

                    if imd_wind is not None and not (0.0 <= imd_wind <= 300.0):
                        imd_wind = None
                    if imd_pres is not None and not (800.0 <= imd_pres <= 1080.0):
                        imd_pres = None

                    imd_avg = (
                        AveragingPeriod.THREE_MINUTE.value
                        if imd_wind is not None
                        else AveragingPeriod.UNKNOWN.value
                    )

                    observations.append(
                        {
                            "source_agency": Agency.IMD.value,
                            "wmo_agency": None,
                            "source_record_id": f"ROW_{line_idx}:NEWDELHI",
                            "observation_time_utc": obs_time_utc,
                            "latitude": imd_lat,
                            "longitude": imd_lon,
                            "geom": WKTElement(f"POINT({imd_lon} {imd_lat})", srid=4326),
                            "wind_speed_knots": imd_wind,
                            "original_wind_speed": imd_wind,
                            "original_wind_unit": "kts",
                            "averaging_period": imd_avg,
                            "central_pressure_hpa": imd_pres,
                            "pressure_drop_hpa": imd_dp,
                            "imd_category": imd_grade,
                            "is_retrospective_best_track": True,
                            "quality_flag": obs_quality,
                            "raw_payload": {
                                "sid": sid,
                                "grade": imd_grade,
                                "ci": parse_clean_float(get_val("NEWDELHI_CI")),
                                "dp": imd_dp,
                                "poci": parse_clean_float(get_val("NEWDELHI_POCI")),
                            },
                        }
                    )

                # 3. JTWC / USA Observation
                usa_wind_raw = get_val("USA_WIND")
                usa_pres_raw = get_val("USA_PRES")
                usa_status = parse_clean_str(get_val("USA_STATUS"))
                usa_lat_raw = get_val("USA_LAT")
                usa_lon_raw = get_val("USA_LON")

                has_usa = any([usa_wind_raw, usa_pres_raw, usa_status, usa_lat_raw, usa_lon_raw])
                if has_usa:
                    usa_lat = parse_clean_float(usa_lat_raw) or main_lat
                    usa_lon = parse_clean_float(usa_lon_raw) or main_lon
                    usa_wind = parse_clean_float(usa_wind_raw)
                    usa_pres = parse_clean_float(usa_pres_raw)

                    if usa_wind is not None and not (0.0 <= usa_wind <= 300.0):
                        usa_wind = None
                    if usa_pres is not None and not (800.0 <= usa_pres <= 1080.0):
                        usa_pres = None

                    usa_avg = (
                        AveragingPeriod.ONE_MINUTE.value
                        if usa_wind is not None
                        else AveragingPeriod.UNKNOWN.value
                    )

                    observations.append(
                        {
                            "source_agency": Agency.JTWC.value,
                            "wmo_agency": None,
                            "source_record_id": f"ROW_{line_idx}:USA",
                            "observation_time_utc": obs_time_utc,
                            "latitude": usa_lat,
                            "longitude": usa_lon,
                            "geom": WKTElement(f"POINT({usa_lon} {usa_lat})", srid=4326),
                            "wind_speed_knots": usa_wind,
                            "original_wind_speed": usa_wind,
                            "original_wind_unit": "kts",
                            "averaging_period": usa_avg,
                            "central_pressure_hpa": usa_pres,
                            "pressure_drop_hpa": None,
                            "imd_category": None,
                            "is_retrospective_best_track": True,
                            "quality_flag": obs_quality,
                            "raw_payload": {
                                "sid": sid,
                                "atcf_id": usa_atcf_id,
                                "status": usa_status,
                                "sshs": parse_clean_float(get_val("USA_SSHS")),
                            },
                        }
                    )

                processed_rows += 1
                yield storm_info, observations
