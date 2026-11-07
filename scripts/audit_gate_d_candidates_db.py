import json
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import Storm, TrackObservation

with open("reports/F2_4_GATE_D_CANDIDATE_INVENTORY.json") as f:
    inv = json.load(f)

candidates = inv["candidate_cohort"]
engine = create_engine(settings.DATABASE_URL)

print("=== CANDIDATE INVENTORY AUDIT AGAINST POSTGRESQL ===")
with Session(engine) as session:
    for c in candidates:
        cid = c["candidate_id"]
        name = c["storm_name"]
        sid = c["canonical_sid"]
        target_utc = datetime.fromisoformat(c["synoptic_target_utc"])

        # Look up storm in DB
        storm = (
            session.execute(
                select(Storm).where(Storm.canonical_name.ilike(f"%{name.split('_')[0]}%"))
            )
            .scalars()
            .first()
        )
        if not storm:
            print(f"[{cid}] {name} ({sid}): STORM NOT FOUND IN DB!")
            continue

        # Look up track observations at synoptic target time
        obs_list = (
            session.execute(
                select(TrackObservation).where(
                    TrackObservation.storm_id == storm.id,
                    TrackObservation.observation_time_utc == target_utc,
                )
            )
            .scalars()
            .all()
        )

        imd_obs = next((o for o in obs_list if o.source_agency == "IMD"), None)
        jtwc_obs = next((o for o in obs_list if o.source_agency == "JTWC"), None)
        ibtracs_obs = next((o for o in obs_list if o.source_agency == "IBTRACS"), None)

        imd_wind = imd_obs.wind_speed_knots if imd_obs else None
        imd_cat = imd_obs.imd_category if imd_obs else None
        jtwc_wind = jtwc_obs.wind_speed_knots if jtwc_obs else None

        print(f"[{cid}] {name:15s} | SID: {sid} | Time: {c['synoptic_target_utc']}")
        print(
            f"   MOSDAC: gId={c['mosdac_gid']} | File={c['filename']} | ExpSize={c['expected_size_bytes']:,} B"
        )
        print(
            f"   IMD  Obs: Wind={imd_wind} kt, Cat={imd_cat}, ID={imd_obs.id if imd_obs else None}"
        )
        print(f"   JTWC Obs: Wind={jtwc_wind} kt, ID={jtwc_obs.id if jtwc_obs else None}")
        print(
            f"   IBTrACS:  Wind={ibtracs_obs.wind_speed_knots if ibtracs_obs else None} kt, WMO={ibtracs_obs.wmo_agency if ibtracs_obs else None}"
        )
