"""Comprehensive security and secret scanning audit for Vayumarg 3.0.

Detects:
1. Blocked binary and dataset extensions (.pt, .h5, etc.) and protected directories.
2. API tokens, OAuth keys, and private key blocks.
3. Database connection URLs with embedded credentials (PostgreSQL, MySQL, etc.).
4. Hardcoded password assignments in application code and reports.
5. Scans current PR commit range, active working tree, and optionally full git history.
"""

import argparse
import os
import re
import subprocess
import sys


DISALLOWED_EXTENSIONS = {
    ".pt", ".pth", ".bin", ".h5", ".hdf5", ".nc", ".nc4", ".grib",
    ".tif", ".tiff", ".env", ".pem", ".key", ".pfx", ".p12", ".sqlite",
}

DISALLOWED_DIRS = {
    "data/raw", "data/processed", "data/backups", "models/vayumarg"
}

SAFE_PASSWORD_PLACEHOLDERS = {
    "", "***", "placeholder", "your_password", "dummy", "test_password",
    "password", "pass", "postgres", "secret", "change_me", "none"
}

SECRET_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"ya29\.[a-zA-Z0-9_\-]+", "Google OAuth Token"),
    (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----", "Private Key Block"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"(?i)api_key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "API Key Literal"),
    # Credential-bearing DB connection string: postgresql://user:pass@host
    (r"(?i)(?:postgres(?:ql)?(?:\+[a-zA-Z0-9_-]+)?)://(?P<user>[^:\s@]+):(?P<pass>[^@\s/]+)@(?P<host>[^/\s:]+)", "Database URL with Password"),
    # Hardcoded password assignments
    (r"(?i)(?:postgres_password|db_password)\s*[:=]\s*['\"](?P<pass>[^'\"]+)['\"]", "Database Password Assignment"),
]


def is_safe_password(pwd: str) -> bool:
    """Check if a detected password is an approved masked placeholder or template."""
    cleaned = pwd.strip().lower()
    return (
        cleaned in SAFE_PASSWORD_PLACEHOLDERS
        or "***" in cleaned
        or (cleaned.startswith("<") and cleaned.endswith(">"))
        or "placeholder" in cleaned
        or "your_" in cleaned
        or "change_this" in cleaned
        or cleaned.startswith("${")  # docker-compose env var interpolation
        or cleaned.startswith("$env:")  # PowerShell env var interpolation
        or "ci_password" in cleaned  # Ephemeral CI runner container fixture in .github/workflows
        or "secure_password" in cleaned  # Disposable CI container password in .github/workflows
    )


def scan_text_content(text: str, context_label: str) -> list[str]:
    """Scan arbitrary text against secret regex patterns."""
    violations = []
    for pattern, desc in SECRET_PATTERNS:
        for match in re.finditer(pattern, text):
            # Check if this pattern matched a password group
            group_dict = match.groupdict()
            if "pass" in group_dict:
                pwd_val = group_dict["pass"]
                if is_safe_password(pwd_val):
                    continue
                violations.append(
                    f"{context_label}: Credential detected ({desc}) with length {len(pwd_val)} chars"
                )
            else:
                raw_match = match.group(0)
                violations.append(
                    f"{context_label}: Token detected ({desc}): {raw_match[:15]}..."
                )
    return violations


def run_security_scan(full_history: bool = False) -> None:
    print("=" * 65)
    print("VAYUMARG 3.0 — PRE-PUBLICATION SECURITY AUDIT")
    print("=" * 65)

    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print(f"Active Branch:  {branch}")
    print(f"HEAD Commit:    {head}")

    remote_main = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
    print(f"origin/main:    {remote_main}")
    assert remote_main == "d467a1c0cd22a07c4cdd5376ca8c9bd9851d22b4", "origin/main has moved!"

    tag_target = subprocess.check_output(["git", "rev-parse", "v3.0.0-pre-refactor-baseline^{commit}"], text=True).strip()
    print(f"Baseline Tag:   {tag_target}")
    assert tag_target == "288fd2cd61b9ec81cdef6ee939559d7a53adc480", "Baseline tag has moved!"

    # 1. Audit changed files in PR #1
    diff_files = subprocess.check_output(["git", "diff", "--name-only", "origin/main..HEAD"], text=True).splitlines()
    print(f"\nChanged Files in PR #1: {len(diff_files)}")

    violations: list[str] = []
    for f in diff_files:
        ext = os.path.splitext(f)[1].lower()
        if ext in DISALLOWED_EXTENSIONS:
            violations.append(f"Disallowed file extension: {f}")
        for b_dir in DISALLOWED_DIRS:
            if f.startswith(b_dir):
                violations.append(f"Disallowed publication directory: {f}")

    # 2. Audit diff text of PR #1 (Only net added lines)
    diff_text = subprocess.check_output(["git", "diff", "origin/main"], text=True, errors="replace")
    added_lines = "\n".join(
        line[1:] for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    violations.extend(scan_text_content(added_lines, "PR #1 Diff (Working Tree Net Additions)"))

    # 3. Audit commit log in PR #1 commit by commit
    pr_commits = subprocess.check_output(
        ["git", "rev-list", "origin/main..HEAD"], text=True
    ).splitlines()
    print(f"Auditing {len(pr_commits)} commits in PR #1 branch history...")
    for commit_sha in pr_commits:
        commit_diff = subprocess.check_output(
            ["git", "show", commit_sha], text=True, errors="replace"
        )
        c_short = commit_sha[:8]
        # Only scan added lines in each commit
        added_in_commit = "\n".join(
            line[1:] for line in commit_diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        commit_violations = scan_text_content(added_in_commit, f"Commit {c_short}")
        if commit_violations:
            for cv in commit_violations:
                print(f"  [HISTORICAL ALERT] {cv}")

    # 4. Optional full repository history scan
    if full_history:
        print("\nScanning entire repository history (all branches)...")
        all_commits = subprocess.check_output(["git", "rev-list", "--all"], text=True).splitlines()
        print(f"Auditing total {len(all_commits)} commits across all refs...")
        for csha in all_commits:
            cdiff = subprocess.check_output(["git", "show", csha], text=True, errors="replace")
            h_violations = scan_text_content(cdiff, f"History Commit {csha[:8]}")
            for hv in h_violations:
                print(f"  [ALL-HISTORY ALERT] {hv}")

    print("-" * 65)
    if violations:
        print("\nCRITICAL SECURITY VIOLATIONS DETECTED IN PR DIFF:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("\nPASSED: PR diff contains zero unmasked credentials or blocked files.")
        print("Ready for screened publication.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Security audit and secret scanner.")
    parser.add_argument("--full-history", action="store_true", help="Scan full git history.")
    args = parser.parse_args()
    run_security_scan(full_history=args.full_history)
