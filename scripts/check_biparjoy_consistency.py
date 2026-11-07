"""Check BIPARJOY forecast consistency across issue times."""

from fastapi.testclient import TestClient

from vayumarg.api.server import app

client = TestClient(app)

print("--- BIPARJOY Demo Case in server.py DEMO_SCENARIOS ---")
scenarios = client.get("/api/demo/scenarios").json()
for s in scenarios:
    if s["storm_name"] == "BIPARJOY":
        print("Scenario config:", s)

times = [
    "2023-06-11T06:00:00Z",
    "2023-06-12T00:00:00Z",
    "2023-06-12T06:00:00Z",
    "2023-06-12T23:58:00Z",
]

for t in times:
    print(f"\n--- Forecast at issue time: {t} ---")
    r = client.post(
        "/api/forecast/generate",
        json={"storm_name": "BIPARJOY", "issue_time_utc": t, "agency": "IMD"},
    )
    if r.status_code == 200:
        d = r.json()
        print("Mean track error km:", d.get("mean_track_error_km"))
        for v in d.get("verification", []):
            print(
                f"  +{v.get('lead_time_hours')}h: track_error_km = {v.get('track_error_km')}, actual = ({v.get('actual_latitude')}, {v.get('actual_longitude')}), pred = ({v.get('predicted_latitude')}, {v.get('predicted_longitude')})"
            )
    else:
        print("Error:", r.status_code, r.text)
