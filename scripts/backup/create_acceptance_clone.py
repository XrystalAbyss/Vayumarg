"""Safe Isolated Database Acceptance Cloning Tool.

Provides secure, non-destructive cloning of the PostGIS research database
into an isolated acceptance test environment using PostgreSQL TEMPLATE mode.

Safeguards enforced:
1. Strict re.fullmatch name validation against SQL injection and invalid characters.
2. Complete parameterization using psycopg.sql.Identifier for all dynamic identifiers.
3. Explicit source database allowlist and disposable clone target allowlist.
4. Absolute protection of primary research database ('vayumarg') and PostgreSQL system databases.
5. Fail-if-exists default policy; requires explicit --force-replace AND --confirm-destructive-replace.
6. Zero hardcoded passwords; connection details loaded strictly from environment or secure CLI args.
7. Verification of primary database identity and schema integrity.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import NoReturn
import psycopg
from psycopg import sql


# Strict naming patterns (PostgreSQL identifier constraints)
DB_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]{1,62}$")

ALLOWED_SOURCE_DATABASES = {"vayumarg", "vayumarg_test"}

ALLOWED_CLONE_TARGET_PATTERNS = [
    re.compile(r"^vayumarg_acceptance_clone$"),
    re.compile(r"^[a-z][a-z0-9_]*_acceptance_clone$"),
    re.compile(r"^[a-z][a-z0-9_]*_clone$"),
    re.compile(r"^[a-z][a-z0-9_]*_test$"),
]

RESTRICTED_DATABASE_NAMES = {
    "vayumarg",
    "postgres",
    "template0",
    "template1",
    "template_postgis",
}


# --- Custom Exception Hierarchy for Deterministic Security Testing ---


class CloneSecurityError(Exception):
    """Base exception for all acceptance clone safety violations."""


class InvalidDatabaseNameError(CloneSecurityError):
    """Raised when a database name contains invalid or unsafe characters."""


class UnauthorizedSourceError(CloneSecurityError):
    """Raised when source database is not in the explicit source allowlist."""


class UnauthorizedTargetError(CloneSecurityError):
    """Raised when target database is not in the disposable target allowlist."""


class ProtectedDatabaseError(CloneSecurityError):
    """Raised when an operation targets a protected or system database."""


class IdenticalSourceDestinationError(CloneSecurityError):
    """Raised when source and destination database names are identical."""


class ExistingCloneRefusalError(CloneSecurityError):
    """Raised when target clone already exists and replacement is not approved."""


class DestructiveConfirmationRequiredError(CloneSecurityError):
    """Raised when --force-replace is set without explicit destructive confirmation."""


class DatabaseNotFoundError(CloneSecurityError):
    """Raised when the specified source database does not exist."""


class AuthenticationFailureError(CloneSecurityError):
    """Raised when database connection authentication fails."""


def validate_database_name(name: str, label: str = "Database") -> str:
    """Validate database identifier strictly using re.fullmatch."""
    if not isinstance(name, str):
        raise InvalidDatabaseNameError(f"{label} name must be a string, got {type(name).__name__}.")
    
    cleaned = name.strip()
    if not DB_NAME_REGEX.fullmatch(cleaned):
        raise InvalidDatabaseNameError(
            f"{label} name '{name}' is invalid. Must match strict identifier format "
            f"[a-z][a-z0-9_]{{1,62}} with no spaces, quotes, hyphens, or semicolons."
        )
    return cleaned


def is_allowed_source_db(source_name: str) -> bool:
    """Check if the source database is explicitly permitted."""
    return source_name in ALLOWED_SOURCE_DATABASES


def is_allowed_clone_target(target_name: str) -> bool:
    """Check if target name conforms to disposable clone allowlist conventions."""
    if target_name in RESTRICTED_DATABASE_NAMES:
        return False
    return any(p.fullmatch(target_name) for p in ALLOWED_CLONE_TARGET_PATTERNS)


def verify_primary_database_identity(cur: psycopg.Cursor, source_db: str) -> None:
    """Verify that the source database exists, is connectable, and is authentic."""
    cur.execute(
        "SELECT datname, datistemplate, datallowconn FROM pg_database WHERE datname = %s;",
        (source_db,),
    )
    row = cur.fetchone()
    if not row:
        raise DatabaseNotFoundError(f"Source database '{source_db}' does not exist on this server.")
    
    datname, is_template, allow_conn = row
    if is_template:
        raise CloneSecurityError(f"Database '{source_db}' is marked as template; invalid normal source.")
    if not allow_conn:
        raise CloneSecurityError(f"Database '{source_db}' does not allow user connections.")

    # If source is primary 'vayumarg', verify core schema authenticity
    if source_db == "vayumarg":
        cur.execute(
            """
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('storms', 'track_observations');
            """
        )
        found_tables = cur.fetchone()[0]
        if found_tables < 1:
            raise CloneSecurityError(
                f"Source database '{source_db}' exists but lacks primary Vayumarg tables. Refusing clone."
            )


def clone_database(
    source_db: str,
    clone_db: str,
    force_replace: bool = False,
    confirm_destructive_replace: bool = False,
    host: str = "127.0.0.1",
    port: int = 5433,
    user: str = "vayumarg_user",
    password: str = "",
) -> dict[str, str | int]:
    """Safely clone source_db into clone_db using PostgreSQL template mode."""
    # 1. Strict re.fullmatch name validation
    clean_source = validate_database_name(source_db, label="Source database")
    clean_clone = validate_database_name(clone_db, label="Target clone database")

    # 2. Source database allowlist check
    if not is_allowed_source_db(clean_source):
        raise UnauthorizedSourceError(
            f"Source database '{clean_source}' is not in the allowed sources: {sorted(ALLOWED_SOURCE_DATABASES)}"
        )

    # 3. Target database allowlist check
    if not is_allowed_clone_target(clean_clone):
        raise UnauthorizedTargetError(
            f"Target database '{clean_clone}' is not permitted. Must match disposable naming "
            f"conventions (*_acceptance_clone, *_clone, *_test) and must not be protected."
        )

    # 4. Strict protection of primary and system databases
    if clean_clone in RESTRICTED_DATABASE_NAMES:
        raise ProtectedDatabaseError(
            f"Target database '{clean_clone}' is in protected system databases list: {RESTRICTED_DATABASE_NAMES}"
        )

    # 5. Prevent identical source and destination
    if clean_source == clean_clone:
        raise IdenticalSourceDestinationError(
            f"Source database '{clean_source}' and clone target '{clean_clone}' cannot be identical."
        )

    conn_params: dict[str, str | int] = {
        "host": host,
        "port": port,
        "user": user,
        "dbname": "postgres",
    }
    if password:
        conn_params["password"] = password

    try:
        with psycopg.connect(**conn_params, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 6. Verify source database identity
                verify_primary_database_identity(cur, clean_source)

                # 7. Check if target clone already exists
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;",
                    (clean_clone,),
                )
                clone_exists = bool(cur.fetchone())

                if clone_exists:
                    if not force_replace:
                        raise ExistingCloneRefusalError(
                            f"Target clone database '{clean_clone}' already exists. "
                            "Refusing to drop or overwrite without explicit opt-in flag (--force-replace)."
                        )
                    if not confirm_destructive_replace:
                        raise DestructiveConfirmationRequiredError(
                            f"Destructive replacement of '{clean_clone}' requires explicit confirmation "
                            "via --confirm-destructive-replace flag."
                        )

                    # Terminate active sessions targeting ONLY the disposable clone
                    cur.execute(
                        """
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s AND pid <> pg_backend_pid();
                        """,
                        (clean_clone,),
                    )

                    # Safe parameterization using psycopg.sql.Identifier
                    drop_stmt = sql.SQL("DROP DATABASE {}").format(sql.Identifier(clean_clone))
                    cur.execute(drop_stmt)

                # 8. Create fresh clone via template using psycopg.sql.Identifier
                create_stmt = sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                    sql.Identifier(clean_clone),
                    sql.Identifier(clean_source),
                )
                cur.execute(create_stmt)

        # 9. Verify clone integrity
        verify_params = dict(conn_params)
        verify_params["dbname"] = clean_clone
        with psycopg.connect(**verify_params) as verify_conn:
            with verify_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema = 'public';
                    """
                )
                table_count = cur.fetchone()[0]

        return {
            "status": "SUCCESS",
            "source": clean_source,
            "target": clean_clone,
            "tables_verified": table_count,
        }

    except psycopg.OperationalError as e:
        err_msg = str(e).lower()
        if "password authentication failed" in err_msg or "authentication failed" in err_msg:
            raise AuthenticationFailureError(f"Database authentication failed for user '{user}'.") from e
        raise CloneSecurityError(f"Database operational connection error: {e}") from e
    except psycopg.Error as e:
        raise CloneSecurityError(f"PostgreSQL engine error: {e}") from e


def get_connection_config(args: argparse.Namespace) -> dict[str, str | int]:
    """Resolve database connection parameters safely from environment."""
    host = args.host or os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(args.port or os.getenv("POSTGRES_PORT", "5433"))
    user = args.user or os.getenv("POSTGRES_USER", "vayumarg_user")
    password = os.getenv("POSTGRES_PASSWORD", "")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safe non-destructive database cloner for Vayumarg acceptance testing."
    )
    parser.add_argument(
        "--source-db",
        default="vayumarg",
        help="Source PostgreSQL database to use as template (default: vayumarg).",
    )
    parser.add_argument(
        "--clone-db",
        default="vayumarg_acceptance_clone",
        help="Target disposable clone database name (default: vayumarg_acceptance_clone).",
    )
    parser.add_argument(
        "--force-replace",
        action="store_true",
        help="Explicitly allow replacing an existing clone database.",
    )
    parser.add_argument(
        "--confirm-destructive-replace",
        action="store_true",
        help="Mandatory confirmation to drop and recreate the disposable clone.",
    )
    parser.add_argument("--host", default=None, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=None, help="PostgreSQL port.")
    parser.add_argument("--user", default=None, help="PostgreSQL user.")

    args = parser.parse_args()
    config = get_connection_config(args)

    try:
        result = clone_database(
            source_db=args.source_db,
            clone_db=args.clone_db,
            force_replace=args.force_replace,
            confirm_destructive_replace=args.confirm_destructive_replace,
            host=str(config["host"]),
            port=int(config["port"]),
            user=str(config["user"]),
            password=str(config["password"]),
        )
        print("=" * 70)
        print("VAYUMARG SAFE ACCEPTANCE CLONING SUCCESSFUL")
        print(f"Source Database:   {result['source']}")
        print(f"Target Clone:      {result['target']}")
        print(f"Tables Verified:   {result['tables_verified']}")
        print("=" * 70)
    except CloneSecurityError as e:
        print(f"\n[CLONE SAFETY VIOLATION BLOCKED]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
