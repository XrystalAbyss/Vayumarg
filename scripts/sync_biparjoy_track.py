"""Ensure BIPARJOY_track.json contains the authoritative IMD coordinates and multi-agency fields."""

import json
from pathlib import Path

# Load from 2023156N10067_track.json
with open("data/demo_cache/storms/2023156N10067_track.json", encoding="utf-8") as f:
    all_obs = json.load(f)

# Group by time
by_time = {}
for o in all_obs:
    t = o.get("observation_time_utc")
    if not t:
        continue
    t_str = str(t)
    if t_str not in by_time:
        by_time[t_str] = {
            "observation_time_utc": t_str,
            "iso_time": t_str,
            "latitude": o.get("latitude"),
            "longitude": o.get("longitude"),
            "imd_wind_speed_knots": None,
            "jtwc_wind_speed_knots": None,
            "wind_speed_knots": o.get("wind_speed_knots"),
            "central_pressure_hpa": o.get("central_pressure_hpa"),
            "imd_category": o.get("imd_category"),
            "source_agency": o.get("source_agency"),
        }
    entry = by_time[t_str]
    agency = o.get("source_agency")
    if agency == "IMD":
        # Authoritative IMD coordinates and wind
        entry["latitude"] = o.get("latitude")
        entry["longitude"] = o.get("longitude")
        entry["imd_wind_speed_knots"] = o.get("wind_speed_knots")
        entry["wind_speed_knots"] = o.get("wind_speed_knots")
        entry["imd_category"] = o.get("imd_category")
        if o.get("central_pressure_hpa") is not None:
            entry["central_pressure_hpa"] = o.get("central_pressure_hpa")
    elif agency == "JTWC":
        entry["jtwc_wind_speed_knots"] = o.get("wind_speed_knots")

clean_list = sorted(by_time.values(), key=lambda x: x["iso_time"])

p = Path("data/demo_cache/storms/BIPARJOY_track.json")
p.write_text(json.dumps(clean_list, indent=2), encoding="utf-8")
print(f"Updated {p} with {len(clean_list)} multi-agency synchronized fixes.")
