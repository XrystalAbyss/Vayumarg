"""GitHub API helper for inspecting actions and opening PR."""

import json
import subprocess
import requests


def get_token():
    p = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = p.communicate("protocol=https\nhost=github.com\n\n")
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def list_actions():
    token = get_token()
    if not token:
        print("No GitHub token available.")
        return []
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.get(
        "https://api.github.com/repos/XrystalAbyss/Vayumarg/actions/runs",
        headers=headers,
    )
    if r.status_code == 200:
        runs = r.json().get("workflow_runs", [])
        print(f"Total workflow runs: {len(runs)}")
        for run in runs[:5]:
            print(
                f"Run ID: {run['id']} | Name: {run['name']} | Status: {run['status']} | "
                f"Conclusion: {run['conclusion']} | Branch: {run['head_branch']} | "
                f"SHA: {run['head_sha'][:7]} | URL: {run['html_url']}"
            )
        return runs
    else:
        print(f"Error {r.status_code}: {r.text[:200]}")
        return []


def open_pr():
    token = get_token()
    if not token:
        print("No GitHub token available.")
        return None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    # Check existing PRs
    r_check = requests.get(
        "https://api.github.com/repos/XrystalAbyss/Vayumarg/pulls?head=XrystalAbyss:feat/v3-p1-backend-stabilization&state=all",
        headers=headers,
    )
    if r_check.status_code == 200 and r_check.json():
        pr = r_check.json()[0]
        print(f"Existing Pull Request found: #{pr['number']} -> {pr['html_url']}")
        return pr

    title = "feat(v3): P1.1R-CI Backend Modularization, PostGIS Infrastructure & Parity Acceptance"
    body = r"""## Vayumarg 3.0 — Milestone P1.1R-CI Release Candidate

### 1. Executive Summary
This PR transitions the historical Vayumarg research prototype into a stabilized, modular scientific architecture with complete API contract parity and verified numerical reproducibility.

### 2. Core Contributions & Scientific Evidence
- **Backend Modularization**: Decoupled monolithic `server.py` (1,151 lines) into thin routing composition (98 lines) with isolated routers in `src/vayumarg/api/routers/` and domain services in `src/vayumarg/services/`.
- **OpenAPI Contract Fidelity**: 100% preservation across all 47 endpoints and HTTP methods. Implemented dual-SID serialization (`canonical_sid` and `storm_sid`) for full backwards and forward client compatibility.
- **Scientific Evidence Reconciliation**: Corrected empirical benchmark tables in `README.md` from authentic evaluation evidence (`hybrid_track_evaluation_summary.json`):
  - Pure GRU: +6h 42.19 km, +12h 89.77 km, +24h 239.35 km
  - Geodesic Extrapolation: +6h 35.32 km, +12h 78.27 km, +24h 180.49 km
  - Vayumarg Hybrid Residual: +6h 33.31 km, +12h 70.62 km, +24h 158.06 km
  - Sequence Window Clarification: 8 fixes $\times$ 3h intervals = 7 intervals = 21.0 elapsed observation hours.
- **13-Item Numerical Parity**: Exact deterministic match across geodesic projections, predictive leakage bounds ($t_{obs} \le t_{issue}$), ISRO INSAT brightness temperature calibration floor ($179.86\text{ K}$), and deep learning forward passes.
- **Model Checkpoint Preservation**: All 4 trained PyTorch models remain byte-exact and SHA-256 verified against private Google Drive cold storage.
- **CI Automation**: Authored 4-job GitHub Actions workflow (`.github/workflows/ci.yml`) featuring isolated unit testing, containerized PostGIS integration testing (`postgis/postgis:16-3.4` on port 5433), Node 20 frontend builds, and scientific contract diffing.

### 3. Scientific Caveats & Research Risk Disclosures
- **Pure GRU Sub-baseline**: Pure recurrent GRU underperforms simple geodesic extrapolation; hybrid residual compensation is mandatory to regain physical trajectory consistency.
- **Exploratory Status of Hybrid Model**: Current benchmark figures reflect exploratory test subsets; untouched confirmatory evaluation on full historical NIO cohorts remains scheduled for Milestone P2.
- **ConvLSTM Spatial Reconstruction**: ConvLSTM visual frame reconstruction demonstrates structural cloud advection learning but does not establish independent intensity forecasting skill.
- **Satellite Coverage Bounds**: Authentic level-1B HDF5 archives remain limited to 4 anchor cyclone acquisitions (AMPHAN, BIPARJOY, REMAL, DANA).
"""
    payload = {
        "title": title,
        "head": "feat/v3-p1-backend-stabilization",
        "base": "main",
        "body": body,
    }
    r = requests.post(
        "https://api.github.com/repos/XrystalAbyss/Vayumarg/pulls",
        headers=headers,
        json=payload,
    )
    if r.status_code in [200, 201]:
        pr = r.json()
        print(f"Created Pull Request: #{pr['number']} -> {pr['html_url']}")
        return pr
    else:
        print(f"Failed to create PR: {r.status_code} {r.text}")
        return None


def list_jobs(run_id):
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.get(
        f"https://api.github.com/repos/XrystalAbyss/Vayumarg/actions/runs/{run_id}/jobs",
        headers=headers,
    )
    if r.status_code == 200:
        jobs = r.json().get("jobs", [])
        for j in jobs:
            print(f"Job ID: {j['id']} | Name: {j['name']} | Status: {j['status']} | Conclusion: {j['conclusion']}")
            for step in j.get("steps", []):
                print(f"   Step: {step['name']} -> status={step['status']}, conclusion={step['conclusion']}")
        return jobs
    else:
        print(f"Error {r.status_code}: {r.text}")
        return []


def get_job_logs(job_id):
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        r = requests.get(
            f"https://api.github.com/repos/XrystalAbyss/Vayumarg/actions/jobs/{job_id}/logs",
            headers=headers,
            allow_redirects=True,
            timeout=30,
        )
        if r.status_code == 200:
            return r.text
        else:
            print(f"Error fetching logs for {job_id}: {r.status_code}")
            return ""
    except Exception as e:
        print(f"Exception fetching logs: {e}")
        return ""


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "logs":
        job_id = sys.argv[2]
        print(f"Fetching logs for job {job_id}...")
        text = get_job_logs(job_id)
        # Print tail of logs or lines matching error/fail
        lines = text.splitlines()
        print(f"Total log lines: {len(lines)}")
        for l in lines[-80:]:
            print(l)
    elif len(sys.argv) > 1:
        run_id = sys.argv[1]
        print(f"Inspecting jobs for run {run_id}...")
        list_jobs(run_id)
    else:
        print("Checking workflow runs...")
        list_actions()
