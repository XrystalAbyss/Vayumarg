"""Integration tests for database safety controls, isolation, and backup recovery."""

import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.backup import backup_database, restore_database
from vayumarg.database.engine import (
    DestructiveOperationBlockedError,
    get_default_engine,
    get_session_factory,
    get_test_engine,
    verify_database_is_disposable,
)
from vayumarg.database.schema import DataSource


@pytest.mark.integration
def test_test_database_isolation(db_session: Session):
    """Verify integration tests strictly execute against isolated test database."""
    engine = db_session.bind
    assert engine is not None
    db_name = engine.url.database
    assert db_name == settings.POSTGRES_TEST_DB
    assert db_name != settings.POSTGRES_DB
    assert "test" in db_name.lower()


@pytest.mark.integration
def test_destructive_operation_blocked_on_production_database():
    """Verify safety guard blocks destructive actions against non-test research database."""
    prod_engine = get_default_engine()
    assert prod_engine.url.database == settings.POSTGRES_DB

    with pytest.raises(DestructiveOperationBlockedError) as exc_info:
        verify_database_is_disposable(prod_engine)

    assert "DESTRUCTIVE_OPERATION_BLOCKED" in str(exc_info.value)
    assert settings.POSTGRES_DB in str(exc_info.value)


@pytest.mark.integration
def test_backup_and_restore_cycle():
    """Verify automated backup and restore of disposable records."""
    temp_backup = Path("data/interim/test_cycle_backup.sql")
    ds_id = uuid.uuid4()
    test_engine = get_test_engine()
    SessionFactory = get_session_factory(test_engine)

    # 1. Insert disposable record
    with SessionFactory() as session:
        ds = DataSource(
            id=ds_id,
            provider_name="BACKUP_CYCLE_PROVIDER",
            dataset_name="BACKUP_CYCLE_DATASET",
            version="v1.0-cycle",
        )
        session.add(ds)
        session.commit()

    try:
        # 2. Run backup
        backup_database(settings.POSTGRES_TEST_DB, temp_backup)
        assert temp_backup.exists()
        assert temp_backup.stat().st_size > 0

        # 3. Delete record
        with SessionFactory() as session:
            record_to_del = session.get(DataSource, ds_id)
            if record_to_del:
                session.delete(record_to_del)
                session.commit()

        with SessionFactory() as session:
            assert session.get(DataSource, ds_id) is None

        # 4. Dispose connection pool before restoring full schema to release table locks
        test_engine.dispose()

        # 5. Restore
        restore_database(settings.POSTGRES_TEST_DB, temp_backup)

        # 6. Verify restored
        with SessionFactory() as session:
            restored = session.get(DataSource, ds_id)
            assert restored is not None
            assert restored.provider_name == "BACKUP_CYCLE_PROVIDER"

            # Cleanup
            session.delete(restored)
            session.commit()
    finally:
        if temp_backup.exists():
            temp_backup.unlink()
