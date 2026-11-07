from fastapi.testclient import TestClient

from vayumarg.api.server import app

client = TestClient(app)
r = client.post(
    "/api/forecast/generate",
    json={"storm_name": "BIPARJOY", "issue_time_utc": "2023-06-11T06:00:00Z", "agency": "IMD"},
)
print("Status:", r.status_code)
d = r.json()
print("Mean track error km:", d.get("mean_track_error_km"))
for v in d.get("verification", []):
    print(
        f"+{v.get('lead_time_hours')}h: err = {v.get('track_error_km')} km, pred = ({v.get('predicted_latitude')}, {v.get('predicted_longitude')}), actual = ({v.get('actual_latitude')}, {v.get('actual_longitude')})"
    )
