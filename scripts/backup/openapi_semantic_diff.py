"""Comprehensive semantic OpenAPI difference analyzer between baseline and current refactored server."""

import json
from pathlib import Path

from vayumarg.api.server import app

BASELINE_PATH = Path("reports/v3/baseline_openapi.json")


def compare_openapi():
    with open(BASELINE_PATH, encoding="utf-8") as f:
        base = json.load(f)
    curr = app.openapi()

    findings = []
    base_paths = set(base.get("paths", {}).keys())
    curr_paths = set(curr.get("paths", {}).keys())

    findings.append(f"Baseline paths count: {len(base_paths)}")
    findings.append(f"Current paths count: {len(curr_paths)}")
    findings.append(f"Missing paths: {sorted(list(base_paths - curr_paths))}")
    findings.append(f"Added paths: {sorted(list(curr_paths - base_paths))}")

    endpoint_discrepancies = []

    for path in sorted(base_paths.intersection(curr_paths)):
        for method in sorted(base["paths"][path].keys()):
            if method not in curr["paths"][path]:
                endpoint_discrepancies.append(f"MISSING METHOD: {method.upper()} on {path}")
                continue
            b_op = base["paths"][path][method]
            c_op = curr["paths"][path][method]

            # Parameters check
            b_params = {param["name"]: param for param in b_op.get("parameters", [])}
            c_params = {param["name"]: param for param in c_op.get("parameters", [])}

            if set(b_params.keys()) != set(c_params.keys()):
                endpoint_discrepancies.append(
                    f"PARAM NAMES MISMATCH {method.upper()} {path}: base={sorted(b_params.keys())}, curr={sorted(c_params.keys())}"
                )

            for pname in b_params:
                if pname in c_params:
                    bp = b_params[pname]
                    cp = c_params[pname]
                    if bp.get("in") != cp.get("in"):
                        endpoint_discrepancies.append(
                            f"PARAM IN MISMATCH {pname} on {method.upper()} {path}: {bp.get('in')} != {cp.get('in')}"
                        )
                    if bp.get("required") != cp.get("required"):
                        endpoint_discrepancies.append(
                            f"PARAM REQUIRED MISMATCH {pname} on {method.upper()} {path}: {bp.get('required')} != {cp.get('required')}"
                        )

            # RequestBody check
            b_has_rb = "requestBody" in b_op
            c_has_rb = "requestBody" in c_op
            if b_has_rb != c_has_rb:
                endpoint_discrepancies.append(
                    f"REQUEST BODY EXISTENCE MISMATCH on {method.upper()} {path}: base={b_has_rb}, curr={c_has_rb}"
                )

            # Response status codes check
            b_resps = set(b_op.get("responses", {}).keys())
            c_resps = set(c_op.get("responses", {}).keys())
            if b_resps != c_resps:
                endpoint_discrepancies.append(
                    f"RESPONSES MISMATCH on {method.upper()} {path}: base={b_resps}, curr={c_resps}"
                )

    print("\n".join(findings))
    print(f"\nTotal Endpoint Parameter / Method / Status Discrepancies: {len(endpoint_discrepancies)}")
    for d in endpoint_discrepancies:
        print("  -", d)

    # Check components schemas
    base_schemas = set(base.get("components", {}).get("schemas", {}).keys())
    curr_schemas = set(curr.get("components", {}).get("schemas", {}).keys())
    print(f"\nBaseline Schemas: {len(base_schemas)}, Current Schemas: {len(curr_schemas)}")
    print(f"Added Schemas: {sorted(list(curr_schemas - base_schemas))}")
    print(f"Missing Schemas: {sorted(list(base_schemas - curr_schemas))}")


if __name__ == "__main__":
    compare_openapi()

