"""Pre-publication security and secret scanning audit for Vayumarg 3.0."""

import os
import re
import subprocess
import sys


def run_security_scan():
    print("=" * 60)
    print("VAYUMARG 3.0 — PRE-PUBLICATION SECURITY AUDIT")
    print("=" * 60)

    # 1. Verify git branch and remote
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print(f"Active Branch: {branch}")
    print(f"HEAD Commit:   {head}")

    # 2. Verify protected main
    remote_main = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
    print(f"origin/main:   {remote_main}")
    assert remote_main == "d467a1c0cd22a07c4cdd5376ca8c9bd9851d22b4", "origin/main has moved!"

    # 3. Verify baseline tag
    tag_target = subprocess.check_output(["git", "rev-parse", "v3.0.0-pre-refactor-baseline^{commit}"], text=True).strip()
    print(f"Baseline Tag:  {tag_target}")
    assert tag_target == "288fd2cd61b9ec81cdef6ee939559d7a53adc480", "Baseline tag has moved!"

    # 4. Check all diff files
    diff_files = subprocess.check_output(["git", "diff", "--name-only", "origin/main..HEAD"], text=True).splitlines()
    print(f"\nChanged Files count: {len(diff_files)}")

    blocked_extensions = {".pt", ".bin", ".h5", ".hdf5", ".nc", ".tif", ".env", ".pem", ".key", ".pfx", ".p12"}
    blocked_dirs = {"data/raw", "data/processed", "models/vayumarg"}

    violations = []
    for f in diff_files:
        ext = os.path.splitext(f)[1].lower()
        if ext in blocked_extensions:
            violations.append(f"Disallowed file extension: {f}")
        for b_dir in blocked_dirs:
            if f.startswith(b_dir):
                violations.append(f"Disallowed publication directory: {f}")

    # 5. Regex secret patterns in diff
    diff_text = subprocess.check_output(["git", "diff", "origin/main..HEAD"], text=True, errors="replace")
    
    patterns = [
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
        (r"ya29\.[a-zA-Z0-9_\-]+", "Google OAuth Token"),
        (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", "Private Key Block"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        (r"(?i)api_key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "API Key Literal"),
    ]

    for pat, desc in patterns:
        matches = re.findall(pat, diff_text)
        for m in matches:
            violations.append(f"Secret detected ({desc}): {m[:20]}...")

    if violations:
        print("\nCRITICAL SECURITY VIOLATIONS DETECTED:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("\nPASSED: Zero secrets, zero binary files, zero credentials detected in diff.")
        print("Ready for screened public publication.")


if __name__ == "__main__":
    run_security_scan()
