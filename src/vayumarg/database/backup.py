"""Database backup and recovery utilities for Vayumarg.

Provides automated, verified snapshot and recovery procedures using PostgreSQL native
tools (pg_dump / psql) executed safely via the isolated PostGIS container.
"""

import subprocess
from pathlib import Path

from vayumarg.core.logging import get_logger
from vayumarg.database.engine import DestructiveOperationBlockedError

logger = get_logger("vayumarg.database.backup")


def backup_database(
    db_name: str,
    output_file: Path | str,
    container_name: str = "vayumarg-postgis",
    user: str = "vayumarg_user",
) -> Path:
    """Create a verified SQL dump of a specified database."""
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Executing pg_dump on database '%s' in container '%s'", db_name, container_name)
    container_dump_path = f"/tmp/{out_path.name}"

    # 1. Run pg_dump inside container
    dump_cmd = [
        "docker",
        "exec",
        container_name,
        "pg_dump",
        "-U",
        user,
        "-d",
        db_name,
        "--clean",
        "--if-exists",
        "-f",
        container_dump_path,
    ]
    res = subprocess.run(dump_cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {res.stderr}")

    # 2. Copy dump out of container to host
    cp_cmd = ["docker", "cp", f"{container_name}:{container_dump_path}", str(out_path)]
    cp_res = subprocess.run(cp_cmd, capture_output=True, text=True, check=False)
    if cp_res.returncode != 0:
        raise RuntimeError(f"docker cp failed: {cp_res.stderr}")

    logger.info(
        "Backup successfully written to %s (size: %d bytes)", out_path, out_path.stat().st_size
    )
    return out_path


def restore_database(
    db_name: str,
    backup_file: Path | str,
    container_name: str = "vayumarg-postgis",
    user: str = "vayumarg_user",
    allow_non_test: bool = False,
) -> bool:
    """Restore a database from a SQL dump with strict safety controls.

    Safety: Refuses to restore into a non-test database unless allow_non_test is explicitly True.
    """
    in_path = Path(backup_file).resolve()
    if not in_path.is_file():
        raise FileNotFoundError(f"Backup file does not exist: {in_path}")

    # Safety validation
    is_test_db = "test" in db_name.lower() or db_name.endswith("_test")
    if not is_test_db and not allow_non_test:
        raise DestructiveOperationBlockedError(
            f"DESTRUCTIVE_OPERATION_BLOCKED: Cannot restore into non-test database '{db_name}' "
            "without explicit allow_non_test=True confirmation."
        )

    logger.info("Restoring backup '%s' into database '%s'", in_path, db_name)
    container_dump_path = f"/tmp/{in_path.name}"

    # 1. Copy dump file into container
    cp_cmd = ["docker", "cp", str(in_path), f"{container_name}:{container_dump_path}"]
    cp_res = subprocess.run(cp_cmd, capture_output=True, text=True, check=False)
    if cp_res.returncode != 0:
        raise RuntimeError(f"docker cp into container failed: {cp_res.stderr}")

    # 2. Execute psql to restore
    restore_cmd = [
        "docker",
        "exec",
        container_name,
        "psql",
        "-U",
        user,
        "-d",
        db_name,
        "-f",
        container_dump_path,
    ]
    res = subprocess.run(restore_cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"psql restore failed: {res.stderr}")

    logger.info("Database '%s' restored successfully from '%s'", db_name, in_path)
    return True
