"""Probe MOSDAC catalog for Gate C Batch 1 candidates: AMPHAN (8353650) and BIPARJOY (11789302)."""

import os

import requests

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.probe_gate_c")

TOKEN_URL = "https://mosdac.gov.in/download_api/gettoken"
DOWNLOAD_URL = "https://mosdac.gov.in/download_api/download"

CANDIDATES = [
    {"name": "AMPHAN", "gid": "8353650", "expected_fn": "3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5"},
    {
        "name": "BIPARJOY",
        "gid": "11789302",
        "expected_fn": "3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5",
    },
]


def get_token() -> str:
    username = os.getenv("MOSDAC_USERNAME") or "ishhangoyal"
    password = os.getenv("MOSDAC_PASSWORD") or "Ishhan@3004"
    resp = requests.post(TOKEN_URL, json={"username": username, "password": password}, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    token = get_token()
    print("Obtained fresh bearer token from MOSDAC.")

    for cand in CANDIDATES:
        print(f"\n--- Probing Candidate: {cand['name']} (gId: {cand['gid']}) ---")
        headers = {
            "Authorization": f"Bearer {token}",
            "Range": "bytes=0-1023",
        }
        params = {"id": cand["gid"]}
        resp = requests.get(DOWNLOAD_URL, headers=headers, params=params, timeout=20)
        print(f"  HTTP Status: {resp.status_code}")
        print(f"  Content-Range: {resp.headers.get('Content-Range')}")
        print(f"  Content-Length: {resp.headers.get('Content-Length')}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        print(f"  Content-Disposition: {resp.headers.get('Content-Disposition')}")

        cr = resp.headers.get("Content-Range", "")
        if "/" in cr:
            total_size = int(cr.split("/")[-1])
            print(
                f"  Confirmed Remote Total Byte Size: {total_size} bytes ({total_size / (1024 * 1024):.2f} MB)"
            )
            cand["confirmed_size"] = total_size


if __name__ == "__main__":
    main()
