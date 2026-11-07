from datetime import UTC, datetime

from sqlalchemy import create_engine, text

from vayumarg.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    query = text("""
        SELECT o.id, o.observation_time_utc, o.latitude, o.longitude, o.wind_speed_knots, o.central_pressure_hpa, o.source_agency
        FROM storms s
        JOIN track_observations o ON s.id = o.storm_id
        WHERE s.canonical_name ILIKE '%DANA%'
          AND o.observation_time_utc >= '2024-10-25 18:00:00'
          AND o.observation_time_utc <= '2024-10-26 06:00:00'
        ORDER BY o.observation_time_utc ASC, o.source_agency ASC
    """)
    res = conn.execute(query).fetchall()

target_time = datetime(2024, 10, 25, 23, 30, tzinfo=UTC)
print(f"Target satellite acquisition: {target_time}")
for r in res:
    dt = abs((r[1] - target_time).total_seconds()) / 60.0
    print(
        f"Agency: {r[6]:<8} Time: {r[1]} | Diff: {dt:5.0f} min | Lat: {r[2]:.2f}, Lon: {r[3]:.2f} | Wind: {r[4]} kt, Press: {r[5]} hPa | ID: {r[0]}"
    )
