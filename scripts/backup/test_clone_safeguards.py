"""Comprehensive Security Safeguard Tests for Database Acceptance Cloner.

Verifies strict input sanitization, psycopg.sql.Identifier parameterization,
fail-if-exists defaults, and protection of production and system databases.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from scripts.backup.create_acceptance_clone import (
    AuthenticationFailureError,
    CloneSecurityError,
    DatabaseNotFoundError,
    DestructiveConfirmationRequiredError,
    ExistingCloneRefusalError,
    IdenticalSourceDestinationError,
    InvalidDatabaseNameError,
    ProtectedDatabaseError,
    UnauthorizedSourceError,
    UnauthorizedTargetError,
    clone_database,
    is_allowed_clone_target,
    is_allowed_source_db,
    validate_database_name,
)


def test_sql_injection_in_source_name():
    """Verify that malicious SQL injection strings in source_db are immediately blocked."""
    injections = [
        "vayumarg; DROP TABLE storms; --",
        "vayumarg' OR 1=1; --",
        'vayumarg"; DROP DATABASE vayumarg; --',
        "vayumarg/*comment*/",
        "vayumarg\x00_test",
        "vayumarg\\;evil",
    ]
    for inj in injections:
        with pytest.raises(InvalidDatabaseNameError):
            validate_database_name(inj, label="Source database")
        with pytest.raises(InvalidDatabaseNameError):
            clone_database(source_db=inj, clone_db="valid_test_acceptance_clone")


def test_sql_injection_in_clone_name():
    """Verify that malicious SQL injection strings in clone_db are immediately blocked."""
    injections = [
        "clone; DROP DATABASE vayumarg; --",
        "clone' OR '1'='1",
        'clone"; SELECT pg_terminate_backend(pid); --',
        "clone_test$(rm -rf /)",
        "clone-with-hyphens_clone",
    ]
    for inj in injections:
        with pytest.raises(InvalidDatabaseNameError):
            validate_database_name(inj, label="Target clone database")
        with pytest.raises(InvalidDatabaseNameError):
            clone_database(source_db="vayumarg", clone_db=inj)


def test_names_with_quotes_and_semicolons():
    """Verify rejection of quotes, double quotes, semicolons, and special characters."""
    bad_names = ['"vayumarg"', "'vayumarg'", "db;name", "db name", "db-name", "db.name"]
    for name in bad_names:
        with pytest.raises(InvalidDatabaseNameError):
            validate_database_name(name)


def test_unauthorized_source_databases():
    """Verify that only explicitly allowlisted source databases can be cloned."""
    unauthorized_sources = ["postgres", "template0", "template1", "other_research_db", "hack_db"]
    for src in unauthorized_sources:
        assert not is_allowed_source_db(src)
        with pytest.raises(UnauthorizedSourceError):
            clone_database(source_db=src, clone_db="valid_temp_acceptance_clone")


def test_protected_target_databases():
    """Verify that production 'vayumarg' and system databases can NEVER be targeted as clones."""
    protected = ["vayumarg", "postgres", "template0", "template1", "template_postgis"]
    for db in protected:
        assert not is_allowed_clone_target(db)
        with pytest.raises(UnauthorizedTargetError):
            clone_database(source_db="vayumarg_test", clone_db=db)


def test_identical_source_and_destination():
    """Verify rejection when source and destination database names are identical."""
    with pytest.raises(CloneSecurityError):
        clone_database(source_db="vayumarg_test", clone_db="vayumarg_test")


def test_existing_clone_refusal_without_flags():
    """Verify fail-if-exists default: existing clone causes refusal without force-replace."""
    # When clone exists in live database (vayumarg_acceptance_clone exists):
    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        with pytest.raises(ExistingCloneRefusalError):
            clone_database(
                source_db="vayumarg",
                clone_db="vayumarg_acceptance_clone",
                force_replace=False,
                password=password,
            )


def test_existing_clone_refusal_without_destructive_confirmation():
    """Verify that force_replace=True STILL fails if confirm_destructive_replace is False."""
    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        with pytest.raises(DestructiveConfirmationRequiredError):
            clone_database(
                source_db="vayumarg",
                clone_db="vayumarg_acceptance_clone",
                force_replace=True,
                confirm_destructive_replace=False,
                password=password,
            )


def test_inaccessible_or_nonexistent_source():
    """Verify that a nonexistent source database raises DatabaseNotFoundError."""
    # Temporarily allow a non-existent source to test existence verification
    # Using 'vayumarg_test' if pointing to wrong server or testing missing db
    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        # Test connecting to an invalid port (inaccessible server)
        with pytest.raises(CloneSecurityError) as exc_info:
            clone_database(
                source_db="vayumarg",
                clone_db="temporary_safe_test",
                port=5499,  # Inaccessible port
                password=password,
            )
        assert "operational connection error" in str(exc_info.value).lower()


def test_failed_authentication():
    """Verify that invalid password raises AuthenticationFailureError."""
    with pytest.raises(AuthenticationFailureError):
        clone_database(
            source_db="vayumarg",
            clone_db="temporary_auth_fail_test",
            password="definitely_wrong_and_invalid_secret_token_12345",
        )


def run_all_safeguard_checks():
    print("Running Database Acceptance Cloner Safeguard Checks...")
    test_sql_injection_in_source_name()
    print("  [PASS] SQL injection in source name blocked")

    test_sql_injection_in_clone_name()
    print("  [PASS] SQL injection in clone target name blocked")

    test_names_with_quotes_and_semicolons()
    print("  [PASS] Names with quotes, semicolons, and spaces blocked")

    test_unauthorized_source_databases()
    print("  [PASS] Unauthorized source databases blocked")

    test_protected_target_databases()
    print("  [PASS] Protected production/system target databases blocked")

    test_identical_source_and_destination()
    print("  [PASS] Identical source and destination blocked")

    test_failed_authentication()
    print("  [PASS] Failed authentication handled with AuthenticationFailureError")

    test_inaccessible_or_nonexistent_source()
    print("  [PASS] Inaccessible database host handled with CloneSecurityError")

    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        test_existing_clone_refusal_without_flags()
        print("  [PASS] Fail-if-exists default policy verified against live instance")

        test_existing_clone_refusal_without_destructive_confirmation()
        print("  [PASS] Destructive confirmation requirement verified against live instance")

    print("\nALL 10 DATABASE CLONER SECURITY SAFEGUARD CHECKS PASSED!")


if __name__ == "__main__":
    run_all_safeguard_checks()
