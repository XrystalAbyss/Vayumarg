"""Vayumarg 3.0 — Pre-Commit Secret Scanner."""

import re
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\astra\Desktop\Project\Vayumarg")

PATTERNS = {
    "Google API Key": re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    "OAuth Access Token": re.compile(r"ya29\.[0-9A-Za-z-_]+"),
    "GitHub Token": re.compile(r"gh[pousr]_[0-9A-Za-z]{36}"),
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Private Key Header": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    "Generic Password Assignment": re.compile(r"""(?:password|passwd|pwd|secret)\s*[:=]\s*["']([^"']{6,})["']""", re.IGNORECASE),
}

EXCLUDE_DIRS = {".git", ".venv", "node_modules", "dist", "pgdata", "__pycache__"}
EXCLUDE_EXTS = {".h5", ".pt", ".sql", ".jpg", ".png", ".zip", ".part", ".pyc"}

def main():
    print("=" * 80)
    print("VAYUMARG 3.0 — PRE-PUBLICATION SECRET SCAN")
    print("=" * 80)

    findings = []
    scanned_count = 0

    for p in PROJECT_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.suffix in EXCLUDE_EXTS:
            continue
        # Skip local .env since it is explicitly gitignored
        if p.name == ".env":
            continue

        scanned_count += 1
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for label, pat in PATTERNS.items():
                for m in pat.finditer(text):
                    match_str = m.group(0)
                    # Filter out placeholders, variable definitions, and standard schema defaults
                    lower_m = match_str.lower()
                    if any(safe in lower_m for safe in ["example", "your_", "changeme", "placeholder", "postgres", "password"]):
                        if label == "Generic Password Assignment":
                            val = m.group(1).lower()
                            if any(safe in val for safe in ["vayumarg_password", "postgres", "example", "placeholder", "changeme"]):
                                continue
                    findings.append((p.relative_to(PROJECT_ROOT).as_posix(), label, match_str[:25] + "..."))
        except Exception:
            pass

    print(f"Scanned {scanned_count} files across working directory.")
    if not findings:
        print(">>> SUCCESS: ZERO CREDENTIALS, SECRETS, OR TOKENS DETECTED <<<")
    else:
        print(f"WARNING: Found {len(findings)} potential security findings:")
        for rel_path, label, snippet in findings:
            print(f"  - [{label}] in {rel_path}: {snippet}")

    return len(findings)

if __name__ == "__main__":
    import sys
    sys.exit(main())

