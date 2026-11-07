from datetime import UTC, datetime

from sqlalchemy import create_engine, select

from vayumarg.core.config import settings
from vayumarg.database.schema import Storm, TrackObservation

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    for name, dt in [
        ("TAUKTAE", datetime(2021, 5, 17, 0, 0, tzinfo=UTC)),
        ("FANI", datetime(2019, 5, 3, 0, 0, tzinfo=UTC)),
        ("FENGAL", datetime(2024, 11, 30, 0, 0, tzinfo=UTC)),
    ]:
        storm = conn.execute(select(Storm).where(Storm.canonical_name == name)).mappings().one()
        obs = (
            conn.execute(
                select(TrackObservation).where(
                    TrackObservation.storm_id == storm["id"],
                    TrackObservation.observation_time_utc == dt,
                )
            )
            .mappings()
            .all()
        )
        print(f"=== {name} at {dt} ===")
        for o in obs:
            print(
                f"  Agency: {o['source_agency']} | Lat: {o['latitude']}, Lon: {o['longitude']} | Wind: {o['wind_speed_knots']} kt | Pres: {o['central_pressure_hpa']} hPa | Cat: {o['imd_category']} | Avg: {o['averaging_period']}"
            )
