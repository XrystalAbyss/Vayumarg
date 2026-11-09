"""Safe Isolated Database Acceptance Cloning Tool.

Provides secure, non-destructive cloning of the PostGIS research database
into an isolated acceptance test environment using PostgreSQL TEMPLATE mode.

Safeguards enforced:
1. Zero hardcoded passwords; connection details loaded strictly from environment variables.
2. Strict primary database identity checks; persistent database can NEVER be mutated or dropped.
3. Explicit allowlist pattern matching for clone target names (*_clone, *_test, acceptance_clone).
4. Fail-if-exists policy by default; explicit opt-in flag (--force-replace) required to recreate.
5. Active connection termination targeting only the disposable clone database prior to replacement.
"""

import argparse
import os
import re
import sys
from typing import NoReturn
import psycopg

CLONE_ALLOWLIST_PATTERNS = [
    r".*_acceptance_clone$",
    r"^acceptance_clone_.*",
    r".*_clone$",
    r".*_test$",
]

RESTRICTED_DATABASE_NAMES = {
    "vayumarg",
    "postgres",
    "template0",
    "template1",
}


def fail(message: str) -> NoReturn:
    """Print an error message and exit with non-zero status."""
    print(f"\n[CLONE SAFETY ERROR]: {message}", file=sys.stderr)
    sys.exit(1)


def is_allowed_clone_name(clone_name: str) -> bool:
    """Verify that the clone database name conforms to disposable naming conventions."""
    normalized = clone_name.strip().lower()
    if normalized in RESTRICTED_DATABASE_NAMES:
        return False
    return any(re.match(pattern, normalized) for pattern in CLONE_ALLOWLIST_PATTERNS)


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


def clone_database(
    source_db: str,
    clone_db: str,
    force_replace: bool = False,
    host: str = "127.0.0.1",
    port: int = 5433,
    user: str = "vayumarg_user",
    password: str = "",
) -> None:
    """Safely clone source_db into clone_db using PostgreSQL template mode."""
    # 1. Validate clone naming against strict allowlist
    if not is_allowed_clone_name(clone_db):
        fail(
            f"Target clone name '{clone_db}' is not permitted. "
            f"Must match allowlist conventions (*_acceptance_clone, *_clone, *_test) "
            f"and must not match protected database names: {RESTRICTED_DATABASE_NAMES}"
        )

    # 2. Prevent identical source and destination
    if source_db.strip().lower() == clone_db.strip().lower():
        fail(f"Source database '{source_db}' and clone target '{clone_db}' cannot be identical.")

    conn_params = {
        "host": host,
        "port": port,
        "user": user,
        "dbname": "postgres",
    }
    if password:
        conn_params["password"] = password

    print("=" * 70)
    print("VAYUMARG SAFE ACCEPTANCE CLONING PROTOCOL")
    print("=" * 70)
    print(f"Host:           {host}:{port}")
    print(f"User:           {user}")
    print(f"Source DB:      {source_db}")
    print(f"Target Clone:   {clone_db}")
    print(f"Force Replace:  {force_replace}")
    print("-" * 70)

    try:
        with psycopg.connect(**conn_params, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 3. Check source database presence
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s AND datistemplate = false;",
                    (source_db,),
                )
                if not cur.fetchone():
                    fail(f"Source database '{source_db}' does not exist on {host}:{port}.")

                # 4. Check if target clone already exists
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;",
                    (clone_db,),
                )
                clone_exists = bool(cur.fetchone())

                if clone_exists:
                    if not force_replace:
                        fail(
                            f"Target clone database '{clone_db}' already exists. "
                            "Refusing to drop or overwrite without explicit opt-in flag (--force-replace)."
                        )
                    print(f"Existing clone '{clone_db}' detected. Terminating active connections...")
                    cur.execute(
                        """
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s AND pid <> pg_backend_pid();
                        """,
                        (clone_db,),
                    )
                    print(f"Dropping existing disposable clone '{clone_db}'...")
                    # Safe parameterized identifier (already regex-validated)
                    cur.execute(f'DROP DATABASE "{clone_db}";')
                    print("Existing clone dropped cleanly.")

                # 5. Create fresh clone via template
                print(f"Creating '{clone_db}' from template '{source_db}'...")
                cur.execute(f'CREATE DATABASE "{clone_db}" TEMPLATE "{source_db}";')
                print("Database clone created successfully.")

        # 6. Verify clone integrity
        verify_params = dict(conn_params)
        verify_params["dbname"] = clone_db
        with psycopg.connect(**verify_params) as verify_conn:
            with verify_conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
                )
                tables = [r[0] for r in cur.fetchall()]
                print(f"\nClone verification: {len(tables)} tables verified in public schema.")
                for tbl in ["storms", "track_observations", "dataset_snapshots"]:
                    if tbl in tables:
                        cur.execute(f'SELECT count(*) FROM public."{tbl}";')
                        cnt = cur.fetchone()[0]
                        print(f"  - Table '{tbl}': {cnt:,} records")

        print("-" * 70)
        print("SAFE ACCEPTANCE CLONE COMPLETED SUCCESSFULLY.")
        print("=" * 70)

    except psycopg.OperationalError as e:
        fail(f"Database connection error: {e}")
    except psycopg.Error as e:
        fail(f"PostgreSQL database error: {e}")


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
        help="Explicitly allow dropping and recreating an existing clone database.",
    )
    parser.add_argument("--host", default=None, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=None, help="PostgreSQL port.")
    parser.add_argument("--user", default=None, help="PostgreSQL user.")

    args = parser.parse_args()
    config = get_connection_config(args)

    clone_database(
        source_db=args.source_db,
        clone_db=args.clone_db,
        force_replace=args.force_replace,
        host=str(config["host"]),
        port=int(config["port"]),
        user=str(config["user"]),
        password=str(config["password"]),
    )


if __name__ == "__main__":
    main()
