"""Deterministic Real-Source Reconciliation Script for Vayumarg.

Compares raw NOAA IBTrACS NI v04r01 CSV records directly against PostgreSQL
track_observations and storms records for 6 diverse historical and modern eras:
1. 1842 - Earliest uninstrumented maritime storm
2. 1932 - Cross-basin trans-continental transit
3. 1951 - Mid-century pre-satellite era cyclone
4. 1966 - Hurricane Faith extreme Arctic extratropical transition
5. 2020 - Super Cyclonic Storm AMPHAN
6. 2023 - Extremely Severe Cyclonic Storm BIPARJOY
"""

import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from vayumarg.core.logging import get_logger
from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import Storm, StormAlias, TrackObservation

logger = get_logger("vayumarg.verify_reconciliation")

CSV_PATH = Path("data/raw/ibtracs_ni_v04r01.csv")

TARGET_STORMS = [
    {"era": "1842 Uninstrumented", "name": "UNNAMED", "year": 1842},
    {"era": "1932 Cross-Basin", "name": "UNNAMED", "year": 1932},
    {"era": "1951 Pre-Satellite", "name": "UNNAMED", "year": 1951},
    {"era": "1966 Arctic Cross-Basin", "name": "FAITH", "year": 1966},
    {"era": "2020 Modern Super Cyclone", "name": "AMPHAN", "year": 2020},
    {"era": "2023 Modern Severe Cyclone", "name": "BIPARJOY", "year": 2023},
]


def run_deterministic_reconciliation() -> dict[str, Any]:
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Missing raw CSV: {CSV_PATH}")

    # Step 1: Scan CSV for target storm SIDs
    print(f"Reading raw CSV: {CSV_PATH}...")
    found_sids: dict[str, dict[str, Any]] = {}

    with open(CSV_PATH, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        next(reader)
        col_map = {name: idx for idx, name in enumerate(header)}

        for row in reader:
            if not row or len(row) <= col_map["SID"]:
                continue
            sid = row[col_map["SID"]].strip()
            name = row[col_map["NAME"]].strip().upper()
            try:
                year = int(row[col_map["SEASON"]].strip())
            except ValueError:
                continue

            for target in TARGET_STORMS:
                t_era = target["era"]
                if t_era in found_sids:
                    continue
                if target["name"] == "FAITH" and "FAITH" in name and year == 1966:
                    found_sids[t_era] = {"sid": sid, "name": name, "year": year}
                elif target["name"] == "AMPHAN" and name == "AMPHAN" and year == 2020:
                    found_sids[t_era] = {"sid": sid, "name": name, "year": year}
                elif target["name"] == "BIPARJOY" and name == "BIPARJOY" and year == 2023:
                    found_sids[t_era] = {"sid": sid, "name": name, "year": year}
                elif target["name"] == "UNNAMED" and year == target["year"]:
                    found_sids[t_era] = {"sid": sid, "name": name, "year": year}

    print(f"Identified benchmark storm SIDs: {found_sids}")

    # Step 2: Compare CSV rows to DB observations for each identified storm
    reconciliation_results = []

    with get_db_session() as session:
        for era, info in found_sids.items():
            sid = info["sid"]
            # Find storm in DB
            storm = (
                session.execute(
                    select(Storm)
                    .join(StormAlias, Storm.id == StormAlias.storm_id)
                    .where(StormAlias.agency_storm_id == sid)
                )
                .scalars()
                .first()
            )

            if not storm:
                print(f"[ERROR] Storm {sid} not found in database!")
                continue

            # Query observations for storm
            db_obs = (
                session.execute(
                    select(TrackObservation)
                    .where(TrackObservation.storm_id == storm.id)
                    .order_by(
                        TrackObservation.observation_time_utc,
                        TrackObservation.source_agency,
                    )
                )
                .scalars()
                .all()
            )

            # Query CSV rows for this SID
            csv_rows = []
            with open(CSV_PATH, encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                h = next(reader)
                next(reader)
                c_map = {name: idx for idx, name in enumerate(h)}
                for row in reader:
                    if row and row[c_map["SID"]].strip() == sid:
                        csv_rows.append(
                            {
                                "iso_time": row[c_map["ISO_TIME"]].strip(),
                                "lat": row[c_map["LAT"]].strip(),
                                "lon": row[c_map["LON"]].strip(),
                                "wmo_wind": row[c_map["WMO_WIND"]].strip(),
                                "wmo_pres": row[c_map["WMO_PRES"]].strip(),
                                "wmo_agency": row[c_map["WMO_AGENCY"]].strip(),
                                "usa_wind": row[c_map["USA_WIND"]].strip(),
                                "newdelhi_wind": row[c_map["NEWDELHI_WIND"]].strip(),
                                "newdelhi_grade": row[c_map["NEWDELHI_GRADE"]].strip(),
                            }
                        )

            # Summary metrics
            agencies_in_db = {o.source_agency for o in db_obs}
            wmo_agencies_in_db = {o.wmo_agency for o in db_obs if o.wmo_agency}
            averaging_in_db = {o.averaging_period for o in db_obs}
            quality_flags = {o.quality_flag for o in db_obs}

            # Check deterministic coordinate alignment for first observation
            first_csv = csv_rows[0]
            first_db = db_obs[0]
            csv_lat = float(first_csv["lat"]) if first_csv["lat"] else None
            csv_lon = float(first_csv["lon"]) if first_csv["lon"] else None

            result_entry = {
                "era": era,
                "sid": sid,
                "name": storm.canonical_name,
                "year": storm.season_year,
                "csv_row_count": len(csv_rows),
                "db_obs_count": len(db_obs),
                "agencies_in_db": sorted(agencies_in_db),
                "wmo_agencies_in_db": sorted(wmo_agencies_in_db),
                "averaging_periods_in_db": sorted(averaging_in_db),
                "quality_flags_in_db": sorted(quality_flags),
                "first_csv_point": {
                    "iso_time": first_csv["iso_time"],
                    "lat": csv_lat,
                    "lon": csv_lon,
                    "wmo_wind": first_csv["wmo_wind"],
                    "wmo_agency": first_csv["wmo_agency"],
                },
                "first_db_point": {
                    "time_utc": first_db.observation_time_utc.isoformat(),
                    "agency": first_db.source_agency,
                    "lat": first_db.latitude,
                    "lon": first_db.longitude,
                    "wind_kts": first_db.wind_speed_knots,
                    "averaging": first_db.averaging_period,
                    "wmo_agency": first_db.wmo_agency,
                    "quality_flag": first_db.quality_flag,
                },
                "coordinate_match": (
                    abs(first_db.latitude - csv_lat) < 1e-4
                    and abs(first_db.longitude - csv_lon) < 1e-4
                ),
            }
            reconciliation_results.append(result_entry)

    out_file = Path("reports/F1_1_SOURCE_RECONCILIATION_SAMPLES.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(reconciliation_results, f, indent=2)

    print(f"Reconciliation results written to {out_file}")
    return {"samples": reconciliation_results}


if __name__ == "__main__":
    run_deterministic_reconciliation()
