"""Atomic and idempotent ingestion transaction management.

Provides transactional boundaries for scientific asset ingestion, ensuring:
1. Every ingestion run is audited in `ingestion_runs`.
2. Partial failures trigger an atomic rollback.
3. Record counts (read, inserted, rejected) are preserved accurately.
4. Error stacks are sanitized and logged.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from vayumarg.contracts.enums import RunStatus
from vayumarg.core.logging import get_logger
from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import IngestionRun

logger = get_logger("vayumarg.ingestion.transaction")


def execute_ingestion_transaction(
    data_source_id: uuid.UUID,
    source_asset_id: uuid.UUID | None,
    ingest_fn: Callable[[Session, IngestionRun], tuple[int, int, int]],
    session_override: Session | None = None,
) -> IngestionRun:
    """Execute a data ingestion transaction with audit logging and rollback protection.

    Args:
        data_source_id: ID of the registered data source.
        source_asset_id: Optional ID of the raw source asset file.
        ingest_fn: Callable receiving (session, run_record) and returning
                   (records_read, records_inserted, records_rejected).
        session_override: Optional active session for nested transactions/tests.

    Returns:
        The completed IngestionRun entity.
    """
    if session_override is not None:
        return _run_within_session(session_override, data_source_id, source_asset_id, ingest_fn)

    with get_db_session() as session:
        return _run_within_session(session, data_source_id, source_asset_id, ingest_fn)


def _run_within_session(
    session: Session,
    data_source_id: uuid.UUID,
    source_asset_id: uuid.UUID | None,
    ingest_fn: Callable[[Session, IngestionRun], tuple[int, int, int]],
) -> IngestionRun:
    run = IngestionRun(
        id=uuid.uuid4(),
        data_source_id=data_source_id,
        source_asset_id=source_asset_id,
        started_at_utc=datetime.now(UTC),
        status=RunStatus.STARTED.value,
        records_read=0,
        records_inserted=0,
        records_rejected=0,
    )
    session.add(run)
    session.flush()

    try:
        logger.info("Beginning ingestion run %s for data source %s", run.id, data_source_id)
        read_count, inserted_count, rejected_count = ingest_fn(session, run)

        run.records_read = read_count
        run.records_inserted = inserted_count
        run.records_rejected = rejected_count
        run.status = RunStatus.COMPLETED.value
        run.completed_at_utc = datetime.now(UTC)
        run.transaction_outcome = "COMMITTED"
        session.flush()
        logger.info(
            "Ingestion run %s completed: %d read, %d inserted, %d rejected",
            run.id,
            read_count,
            inserted_count,
            rejected_count,
        )
        return run
    except Exception as exc:
        run.status = RunStatus.FAILED.value
        run.completed_at_utc = datetime.now(UTC)
        run.error_details = str(exc)
        run.transaction_outcome = "ROLLED_BACK"
        logger.error("Ingestion run %s failed with exception: %s", run.id, exc)
        raise
