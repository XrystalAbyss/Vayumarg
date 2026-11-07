"""Repeatable backup-and-restore demonstration using disposable fixtures."""

import uuid
from pathlib import Path

from vayumarg.core.config import settings
from vayumarg.database.backup import backup_database, restore_database
from vayumarg.database.engine import get_session_factory, get_test_engine
from vayumarg.database.schema import DataSource, Storm


def run_demo() -> None:
    print("=" * 70)
    print("VAYUMARG F0.1: REPEATABLE BACKUP & RESTORE DEMONSTRATION")
    print("=" * 70)

    test_engine = get_test_engine()
    SessionFactory = get_session_factory(test_engine)
    disposable_storm_id = uuid.uuid4()
    disposable_ds_id = uuid.uuid4()

    # 1. Insert Disposable Fixture into vayumarg_test
    with SessionFactory() as session:
        ds = DataSource(
            id=disposable_ds_id,
            provider_name="BACKUP_DEMO_PROVIDER",
            dataset_name="BACKUP_DEMO_DATASET",
            version="1.0-demo",
            citation="Disposable fixture for backup/restore demonstration",
        )
        storm = Storm(
            id=disposable_storm_id,
            canonical_name="DISPOSABLE_DEMO_CYCLONE",
            season_year=2024,
            primary_basin="BOB",
        )
        session.add(ds)
        session.add(storm)
        session.commit()
    print(f"[+] Inserted disposable test storm: {disposable_storm_id}")

    # 2. Perform Backup
    backup_path = Path("data/interim/demo_backup.sql")
    backup_database(settings.POSTGRES_TEST_DB, backup_path)
    print(f"[+] Backup written to: {backup_path} ({backup_path.stat().st_size} bytes)")

    # 3. Simulate Data Loss / Deletion
    with SessionFactory() as session:
        st = session.get(Storm, disposable_storm_id)
        if st:
            session.delete(st)
        d_src = session.get(DataSource, disposable_ds_id)
        if d_src:
            session.delete(d_src)
        session.commit()
    print("[+] Simulated data deletion: records removed from test database.")

    # Verify deletion
    with SessionFactory() as session:
        assert session.get(Storm, disposable_storm_id) is None
    print("[+] Verified test database is in deleted state.")

    # 4. Perform Restore
    restore_database(settings.POSTGRES_TEST_DB, backup_path)
    print("[+] Executed database restore.")

    # 5. Verify Restored Records
    with SessionFactory() as session:
        restored_storm = session.get(Storm, disposable_storm_id)
        restored_ds = session.get(DataSource, disposable_ds_id)
        assert restored_storm is not None, "Storm record failed to restore!"
        assert restored_ds is not None, "DataSource record failed to restore!"
        print(
            f"[+] RESTORE VERIFIED! Restored storm: {restored_storm.canonical_name} ({restored_storm.id})"
        )

        # Cleanup disposable records
        session.delete(restored_storm)
        session.delete(restored_ds)
        session.commit()
    print("[+] Disposable test records cleaned up.")

    # Clean up local backup file
    if backup_path.exists():
        backup_path.unlink()
    print("[SUCCESS] Repeatable backup and restore demonstration completed successfully.")


if __name__ == "__main__":
    run_demo()
