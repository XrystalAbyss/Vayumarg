"""Inspect best-track availability, IMD labels, intensity stages, and timing for candidates."""

from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import Storm, TrackObservation


def inspect_storm_near_time(
    s: Session, storm_name: str, target_time: datetime, time_window_hours: float = 3.0
):
    storm = s.execute(
        select(Storm).where(Storm.canonical_name.ilike(f"%{storm_name}%"))
    ).scalar_one_or_none()
    if not storm:
        print(f"Storm {storm_name} NOT FOUND in database!")
        return

    print("\n=======================================================")
    print(
        f"STORM: {storm.canonical_name} (ID: {storm.id}, Basin: {storm.primary_basin}, Season: {storm.season_year})"
    )
    print(f"Target Satellite Time: {target_time}")

    from datetime import timedelta

    t_min = target_time - timedelta(hours=time_window_hours)
    t_max = target_time + timedelta(hours=time_window_hours)

    stmt = (
        select(TrackObservation)
        .where(
            TrackObservation.storm_id == storm.id,
            TrackObservation.observation_time_utc >= t_min,
            TrackObservation.observation_time_utc <= t_max,
        )
        .order_by(TrackObservation.observation_time_utc, TrackObservation.source_agency)
    )
    obs_list = s.execute(stmt).scalars().all()
    print(f"Observations within +/- {time_window_hours} hours: {len(obs_list)}")
    for o in obs_list:
        dt = (o.observation_time_utc - target_time).total_seconds() / 60.0
        print(
            f"  Agency: {o.source_agency:<8} Time: {o.observation_time_utc} (dt={dt:+6.1f}m) | "
            f"Coords: ({o.latitude:.2f}, {o.longitude:.2f}) | "
            f"Wind: {o.wind_speed_knots} kt ({o.averaging_period}) | "
            f"Press: {o.central_pressure_hpa} hPa | Cat: {o.imd_category}"
        )


def main():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        # 1. REMAL: 27 May 2024 19:15 UTC
        inspect_storm_near_time(s, "REMAL", datetime(2024, 5, 27, 19, 15, tzinfo=UTC))

        # 2. DANA: 25 Oct 2024 23:08 UTC
        inspect_storm_near_time(s, "DANA", datetime(2024, 10, 25, 23, 8, tzinfo=UTC))

        # 3. AMPHAN: 19 May 2020 23:15 UTC
        inspect_storm_near_time(s, "AMPHAN", datetime(2020, 5, 19, 23, 15, tzinfo=UTC))

        # 4. AMPHAN: 19 May 2020 23:58 UTC
        inspect_storm_near_time(s, "AMPHAN", datetime(2020, 5, 19, 23, 58, tzinfo=UTC))

        # 5. BIPARJOY: 12 June 2023 23:58 UTC
        inspect_storm_near_time(s, "BIPARJOY", datetime(2023, 6, 12, 23, 58, tzinfo=UTC))


if __name__ == "__main__":
    main()
