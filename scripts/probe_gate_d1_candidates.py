import requests

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.probe_d1")

MOSDAC_DOWNLOAD_BASE = "https://mosdac.gov.in/download_api/download"

candidates = [
    {
        "storm": "TAUKTAE",
        "gid": "9293840",
        "filename": "3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5",
        "dataset_id": "3RIMG_L1B_STD",
    },
    {
        "storm": "FANI",
        "gid": "7206464",
        "filename": "3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5",
        "dataset_id": "3RIMG_L1B_STD",
    },
    {
        "storm": "FENGAL",
        "gid": "14687507",
        "filename": "3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5",
        "dataset_id": "3SIMG_L1B_STD",
    },
]

print("=== PROBING GATE D1 CANDIDATES VIA OPENSEARCH API ===")
# Query OpenSearch API for exact metadata and file size
for c in candidates:
    url = "https://mosdac.gov.in/apios/datasets.json"
    params = {"datasetId": c["dataset_id"], "gId": c["gid"], "count": 1}
    try:
        r = requests.get(url, params=params, timeout=15.0)
        data = r.json()
        entry = data.get("entries", [{}])[0]
        size_mb = entry.get("sizeMB", "unknown")
        identifier = entry.get("identifier", "unknown")
        print(
            f"[{c['storm']}] gId={c['gid']}: file={identifier}, sizeMB={size_mb}, link={entry.get('link')}"
        )
    except Exception as e:
        print(f"[{c['storm']}] Error probing OpenSearch: {e}")
