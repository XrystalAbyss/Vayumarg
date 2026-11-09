"""Verification script for database clone safeguards."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.backup.create_acceptance_clone import is_allowed_clone_name, clone_database

def run_tests():
    print("Testing is_allowed_clone_name...")
    assert is_allowed_clone_name("vayumarg_acceptance_clone") is True
    assert is_allowed_clone_name("acceptance_clone_20261109") is True
    assert is_allowed_clone_name("research_temp_clone") is True
    assert is_allowed_clone_name("benchmark_test") is True

    # Disallowed: protected production database names
    assert is_allowed_clone_name("vayumarg") is False
    assert is_allowed_clone_name("postgres") is False
    assert is_allowed_clone_name("template0") is False
    assert is_allowed_clone_name("template1") is False

    # Disallowed: arbitrary non-clone names
    assert is_allowed_clone_name("production_data") is False
    assert is_allowed_clone_name("vayumarg_backup") is False
    assert is_allowed_clone_name("analytical_lake") is False
    print("All allowlist checks PASSED.")

    print("\nTesting clone_database guardrails...")
    # 1. Blocks protected clone name
    try:
        clone_database(source_db="vayumarg", clone_db="vayumarg", force_replace=False)
        assert False, "Should have failed on protected clone name"
    except SystemExit:
        print("  - Correctly blocked clone target named 'vayumarg'.")

    # 2. Blocks unauthorized clone name
    try:
        clone_database(source_db="vayumarg", clone_db="unauthorized_db", force_replace=False)
        assert False, "Should have failed on unauthorized clone name"
    except SystemExit:
        print("  - Correctly blocked unauthorized clone target name.")

    # 3. Blocks identical source and target
    try:
        clone_database(source_db="vayumarg_acceptance_clone", clone_db="vayumarg_acceptance_clone", force_replace=True)
        assert False, "Should have failed on identical source and target"
    except SystemExit:
        print("  - Correctly blocked identical source and destination.")

    print("\nALL CLONE SAFEGUARDS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
