"""Unauthenticated MOSDAC catalog discovery for REMAL, DANA, AMPHAN, and BIPARJOY."""

import json
from pathlib import Path

from vayumarg.ingestion.mosdac_client import MOSDACSearchClient

OUT_DIR = Path("reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_STORMS = [
    {
        "name": "REMAL",
        "sid": "2024145N14087",
        "basin": "Bay of Bengal",
        "sensor": "INSAT-3DR",
        "dataset_id": "3RIMG_L1B_STD",
        "start_time": "2024-05-25",
        "end_time": "2024-05-27",
        "stages": [
            ("Pre-intensification", "2024-05-25T06:00:00Z"),
            ("Intensification", "2024-05-26T00:00:00Z"),
            ("Peak Landfall", "2024-05-26T18:02:00Z"),  # Already downloaded
            ("Weakening post-landfall", "2024-05-27T12:00:00Z"),
        ],
    },
    {
        "name": "DANA",
        "sid": "2024295N15092",
        "basin": "Bay of Bengal",
        "sensor": "INSAT-3DS",
        "dataset_id": "3SIMG_L1B_STD",
        "start_time": "2024-10-23",
        "end_time": "2024-10-25",
        "stages": [
            ("Intensification", "2024-10-24T00:00:00Z"),
            ("Peak Landfall", "2024-10-24T18:00:00Z"),
        ],
    },
    {
        "name": "AMPHAN",
        "sid": "2020136N10088",
        "basin": "Bay of Bengal",
        "sensor": "INSAT-3DR",
        "dataset_id": "3RIMG_L1B_STD",
        "start_time": "2020-05-18",
        "end_time": "2020-05-19",
        "stages": [
            ("Super Cyclone Peak", "2020-05-18T12:00:00Z"),
        ],
    },
    {
        "name": "BIPARJOY",
        "sid": "2023156N10067",
        "basin": "Arabian Sea",
        "sensor": "INSAT-3DR",
        "dataset_id": "3RIMG_L1B_STD",
        "start_time": "2023-06-11",
        "end_time": "2023-06-12",
        "stages": [
            ("Arabian Sea Peak ESCS", "2023-06-11T12:00:00Z"),
        ],
    },
]


def run_discovery():
    client = MOSDACSearchClient()
    inventory = {}

    for target in TARGET_STORMS:
        name = target["name"]
        ds_id = target["dataset_id"]
        start_t = target["start_time"]
        end_t = target["end_time"]
        print(f"\nQuerying MOSDAC for {name} ({ds_id}, {start_t} to {end_t})...")
        try:
            # Query count=10 to find available granules
            res = client.search(dataset_id=ds_id, start_time=start_t, end_time=end_t, count=10)
            print(f" -> Found {res.total_results} total results ({res.total_size_mb:.2f} MB)")
            entries = []
            for e in res.entries:
                entries.append(
                    {
                        "identifier": e.identifier,
                        "record_id": e.record_id,
                        "product_date_utc": e.product_date_utc,
                        "dataset_id": e.dataset_id,
                    }
                )
                print(
                    f"    gId: {e.record_id:8s} | file: {e.identifier} | time: {e.product_date_utc}"
                )

            inventory[name] = {
                "storm": name,
                "sid": target["sid"],
                "basin": target["basin"],
                "dataset_id": ds_id,
                "sensor": target["sensor"],
                "total_available_in_window": res.total_results,
                "total_size_mb": res.total_size_mb,
                "sample_entries": entries,
            }
        except Exception as err:
            print(f" -> Error searching {name}: {err}")
            inventory[name] = {"error": str(err)}

    out_file = Path("reports/F2_2_REAL_ASSET_INVENTORY.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    print(f"\nDiscovery inventory written to {out_file}")


if __name__ == "__main__":
    run_discovery()
