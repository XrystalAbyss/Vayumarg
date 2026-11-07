"""Audit exact DANA track observation rows and metadata around 25-26 October 2024."""

from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import Storm, TrackObservation


def main():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        storm = s.execute(select(Storm).where(Storm.canonical_name.ilike("%DANA%"))).scalar_one()
        print(f"Storm: {storm.canonical_name} (ID: {storm.id}, Season: {storm.season_year})")

        t_start = datetime(2024, 10, 25, 12, 0, tzinfo=UTC)
        t_end = datetime(2024, 10, 26, 6, 0, tzinfo=UTC)

        stmt = (
            select(TrackObservation)
            .where(
                TrackObservation.storm_id == storm.id,
                TrackObservation.observation_time_utc >= t_start,
                TrackObservation.observation_time_utc <= t_end,
            )
            .order_by(TrackObservation.observation_time_utc, TrackObservation.source_agency)
        )
        obs_list = s.execute(stmt).scalars().all()

        print(f"\nObservations between {t_start} and {t_end}: {len(obs_list)}")
        for o in obs_list:
            raw = o.raw_payload or {}
            print(f"\nID: {o.id}")
            print(
                f"  Time: {o.observation_time_utc} | Agency: {o.source_agency} | WMO Agency: {o.wmo_agency}"
            )
            print(f"  Coords: Lat={o.latitude}, Lon={o.longitude}")
            print(
                f"  Wind: {o.wind_speed_knots} kt (Original: {o.original_wind_speed} {o.original_wind_unit}, Avg: {o.averaging_period})"
            )
            print(f"  Pressure: {o.central_pressure_hpa} hPa (Drop: {o.pressure_drop_hpa} hPa)")
            print(
                f"  IMD Category: {o.imd_category} | Retrospective: {o.is_retrospective_best_track} | Superseded: {o.is_superseded}"
            )
            print(f"  Raw Keys: {list(raw.keys()) if isinstance(raw, dict) else type(raw)}")
            if isinstance(raw, dict):
                # Print interesting raw keys
                keys_of_interest = [
                    "nature",
                    "track_type",
                    "dist2land",
                    "landfall",
                    "source",
                    "usa_status",
                    "tokyo_grade",
                    "newdelhi_grade",
                ]
                found = {k: raw[k] for k in keys_of_interest if k in raw}
                print(f"  Raw Context: {found}")


if __name__ == "__main__":
    main()
