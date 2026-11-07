"""Comprehensive API test suite for Vayumarg Cyclone Intelligence Studio."""

from fastapi.testclient import TestClient

from vayumarg.api.server import app


def run_all_tests():
    client = TestClient(app)

    print("1. Health Check: /api/health")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Error: {r.status_code} {r.text}"
    health = r.json()
    print("   Status:", health["status"], "| DB:", health["database_backend"])
    assert health["status"] == "OPERATIONAL"

    print("\n2. Summary Check: /api/summary")
    r = client.get("/api/summary")
    assert r.status_code == 200
    summary = r.json()
    print(
        "   Storms:",
        summary["total_historical_storms"],
        "| Obs:",
        summary["total_track_observations"],
    )
    print("   Crops:", summary["total_verified_crops"], "| Mode:", summary["mode"])
    assert summary["total_historical_storms"] >= 1860
    assert summary["total_verified_crops"] >= 4

    print("\n3. Storms List: /api/storms")
    r = client.get("/api/storms?limit=10")
    assert r.status_code == 200
    storms = r.json()
    print(f"   Returned {len(storms)} storms. Sample: {[s['canonical_name'] for s in storms[:5]]}")

    print("\n4. Storm Detail: /api/storms/BIPARJOY")
    r = client.get("/api/storms/BIPARJOY")
    assert r.status_code == 200
    detail = r.json()
    print(
        "   Canonical SID:", detail["canonical_sid"], "| Total Obs:", detail["total_observations"]
    )

    print("\n5. Storm Track: /api/storms/BIPARJOY/track")
    r = client.get("/api/storms/BIPARJOY/track")
    assert r.status_code == 200
    track = r.json()
    print("   Track feature count:", len(track["geojson"]["features"]))

    print("\n6. Storm Satellite Metadata: /api/storms/BIPARJOY/satellite")
    r = client.get("/api/storms/BIPARJOY/satellite")
    assert r.status_code == 200
    sat = r.json()
    print("   Platform:", sat["satellite_platform"], "| Crop:", sat["crop_filename"])

    print("\n7. Satellite Crops List: /api/satellite/crops")
    r = client.get("/api/satellite/crops")
    assert r.status_code == 200
    crops = r.json()
    print("   Available crops:", [c["storm_name"] for c in crops])

    print("\n8. Crop Preview (PNG): /api/satellite/crops/BIPARJOY/preview?channel=TIR-1")
    r = client.get("/api/satellite/crops/BIPARJOY/preview?channel=TIR-1")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    print(f"   PNG Preview Bytes: {len(r.content)}")

    print("\n9. Crop Metrics: /api/satellite/crops/AMPHAN/metrics?channel=TIR-1")
    r = client.get("/api/satellite/crops/AMPHAN/metrics?channel=TIR-1")
    assert r.status_code == 200
    met = r.json()
    t_quant = met.get("temperature_quantiles_kelvin", {})
    c_anal = met.get("cold_cloud_analytics", {})
    print(
        f"   Min K: {t_quant.get('min_kelvin')} | Area < 200K: {c_anal.get('area_under_200k_km2')} km²"
    )
    print(f"   Symmetry Index: {met.get('azimuthal_symmetry_index')}")

    print("\n10. Forecast Generation (POST): /api/forecast/generate")
    fc_req = {"storm_name": "BIPARJOY", "issue_time_utc": "2023-06-11T06:00:00Z", "agency": "IMD"}
    r = client.post("/api/forecast/generate", json=fc_req)
    assert r.status_code == 200, f"Error: {r.status_code} {r.text}"
    fc = r.json()
    print("   Forecast Points count:", len(fc.get("forecast_points", [])))
    print("   Verification count:", len(fc.get("verification", [])))
    print("   Mean Track Error (km):", fc.get("mean_track_error_km"))
    for p in fc.get("forecast_points", []):
        print(
            f"     +{p['lead_time_hours']}h: ({p['predicted_latitude']}, {p['predicted_longitude']}) {p['predicted_wind_speed_knots']} kt ({p['predicted_imd_category']})"
        )

    print("\n11. Forecast GET: /api/storms/BIPARJOY/forecast")
    r = client.get("/api/storms/BIPARJOY/forecast?issue_time_utc=2023-06-11T06:00:00Z&agency=IMD")
    assert r.status_code == 200
    print("   GET Forecast Success. Points:", len(r.json().get("forecast_points", [])))

    print("\n12. Demonstration Scenarios: /api/demo/scenarios")
    r = client.get("/api/demo/scenarios")
    assert r.status_code == 200
    scenarios = r.json()
    print("   Demo Scenarios:", [s["storm_name"] for s in scenarios])
    assert len(scenarios) == 4

    print("\n13. Scientific Governance & Methodology: /api/governance and /api/methodology")
    r1 = client.get("/api/governance")
    r2 = client.get("/api/methodology")
    assert r1.status_code == 200 and r2.status_code == 200
    print("   Governance metrics classifications:", len(r1.json()["metrics_classification"]))
    print("   Methodology title:", r2.json()["title"])

    print("\n14. Single-Page Application: GET /")
    r = client.get("/")
    assert r.status_code == 200
    assert "VAYUMARG" in r.text
    print("   HTML UI served successfully. Length:", len(r.text))

    print("\n=======================================================")
    print(" ALL 14 METEOROLOGICAL API ENDPOINTS VERIFIED 100% OK! ")
    print("=======================================================")


if __name__ == "__main__":
    run_all_tests()
