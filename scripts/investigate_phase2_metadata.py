from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import SatelliteGranule, Storm, TrackObservation

engine = create_engine(settings.DATABASE_URL)

print("=== 1. TAUKTAE INVESTIGATION ===")
with Session(engine) as s:
    st = s.execute(select(Storm).where(Storm.canonical_name == "TAUKTAE")).scalar_one()
    obs_00 = (
        s.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st.id,
                TrackObservation.observation_time_utc == datetime(2021, 5, 17, 0, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )
    obs_03 = (
        s.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st.id,
                TrackObservation.observation_time_utc == datetime(2021, 5, 17, 3, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )

    print("TAUKTAE at 00:00 UTC:")
    for o in obs_00:
        print(
            f"  Agency: {o.source_agency:8s} | Lat: {o.latitude:6.2f} | Lon: {o.longitude:6.2f} | Wind: {o.wind_speed_knots} | Pres: {o.central_pressure_hpa} | Cat: {o.imd_category} | RecID: {o.source_record_id}"
        )
    print("TAUKTAE at 03:00 UTC:")
    for o in obs_03:
        print(
            f"  Agency: {o.source_agency:8s} | Lat: {o.latitude:6.2f} | Lon: {o.longitude:6.2f} | Wind: {o.wind_speed_knots} | Pres: {o.central_pressure_hpa} | Cat: {o.imd_category} | RecID: {o.source_record_id}"
        )

print("\n=== 2. FANI INVESTIGATION ===")
with Session(engine) as s:
    st = s.execute(select(Storm).where(Storm.canonical_name == "FANI")).scalar_one()
    obs_fani = (
        s.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st.id,
                TrackObservation.observation_time_utc == datetime(2019, 5, 3, 0, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )
    print("FANI at 2019-05-03 00:00 UTC:")
    for o in obs_fani:
        print(
            f"  Agency: {o.source_agency:8s} | Lat: {o.latitude:6.2f} | Lon: {o.longitude:6.2f} | Wind: {o.wind_speed_knots} | Pres: {o.central_pressure_hpa} | Cat: {o.imd_category} | RecID: {o.source_record_id} | Raw: {o.raw_payload}"
        )

print("\n=== 3. FENGAL INVESTIGATION ===")
with Session(engine) as s:
    st = s.execute(select(Storm).where(Storm.canonical_name == "FENGAL")).scalar_one()
    obs_fengal = (
        s.execute(
            select(TrackObservation).where(
                TrackObservation.storm_id == st.id,
                TrackObservation.observation_time_utc == datetime(2024, 11, 30, 0, 0, tzinfo=UTC),
            )
        )
        .scalars()
        .all()
    )
    print("FENGAL at 2024-11-30 00:00 UTC:")
    for o in obs_fengal:
        print(
            f"  Agency: {o.source_agency:8s} | Lat: {o.latitude:6.2f} | Lon: {o.longitude:6.2f} | Wind: {o.wind_speed_knots} | Pres: {o.central_pressure_hpa} | Cat: {o.imd_category} | RecID: {o.source_record_id} | Raw: {o.raw_payload}"
        )

print("\n=== 4. REMAL MOSDAC gId INVESTIGATION ===")
with Session(engine) as s:
    gr = (
        s.execute(
            select(SatelliteGranule).where(SatelliteGranule.granule_name.like("%26MAY2024_1802%"))
        )
        .scalars()
        .all()
    )
    for g in gr:
        print(f"Granule in DB: ID={g.id} | Name={g.granule_name} | Metadata={g.granule_metadata}")
