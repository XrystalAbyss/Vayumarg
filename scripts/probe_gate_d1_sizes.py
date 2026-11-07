import os

import requests

token_url = "https://mosdac.gov.in/download_api/gettoken"
download_url = "https://mosdac.gov.in/download_api/download"
username = os.getenv("MOSDAC_USERNAME") or "ishhangoyal"
password = os.getenv("MOSDAC_PASSWORD") or "Ishhan@3004"
r = requests.post(token_url, json={"username": username, "password": password}, timeout=15)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

for name, gid in [
    ("TAUKTAE", "9293840"),
    ("FANI", "7206464"),
    ("FENGAL", "14687507"),
]:
    resp = requests.get(
        download_url,
        headers={**headers, "Range": "bytes=0-0"},
        params={"id": gid},
        timeout=15,
    )
    print(
        f"{name} (gId {gid}): status={resp.status_code}, content_range={resp.headers.get('Content-Range')}, content_disp={resp.headers.get('Content-Disposition')}"
    )
