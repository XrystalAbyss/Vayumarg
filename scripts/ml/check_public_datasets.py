import json
import ssl
import urllib.request

ctx = ssl._create_unverified_context()

print("1. Checking TCIR with unverified context...")
url = "https://www.csie.ntu.edu.tw/~htlin/program/TCIR/"
try:
    with urllib.request.urlopen(url, context=ctx, timeout=10) as res:
        print("   TCIR page status:", res.status)
        import re

        html = res.read().decode("utf-8", errors="ignore")
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        for link_url in links:
            if any(
                k in link_url.lower()
                for k in ["tar", "gz", "h5", "zip", "tcir", "download", "dropbox", "google"]
            ):
                print("   Found link:", link_url[:120])
except Exception as e:
    print("   TCIR error:", e)

print("\n2. Checking NASA Tropical Cyclone Wind files on HuggingFace...")
hf_files_url = (
    "https://huggingface.co/api/datasets/isp-uv-es/nasa-tropical-cyclone-wind-taco/tree/main"
)
try:
    req = urllib.request.Request(hf_files_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
        tree = json.loads(res.read().decode("utf-8"))
        print(f"   Files found: {len(tree)}")
        for item in tree[:15]:
            print(f"   - {item.get('path')} ({item.get('size', 'dir')} bytes)")
except Exception as e:
    print("   HF error:", e)
