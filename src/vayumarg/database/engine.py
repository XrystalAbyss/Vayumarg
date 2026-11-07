"""Database engine and session management for Vayumarg.

Manages PostgreSQL/PostGIS connectivity, connection pooling, transactional contexts,
health checks, PostGIS extension verification, and fallback detection.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from vayumarg.core.config import settings
from vayumarg.core.logging import get_logger
from vayumarg.database.schema import (
    DataQualityIssue,
    DatasetSnapshot,
    DataSource,
    IngestionRun,
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    SatelliteTrackAssociation,
    SourceAsset,
    Storm,
    StormAlias,
    TrackObservation,
)

logger = get_logger("vayumarg.database.engine")


class DestructiveOperationBlockedError(RuntimeError):
    """Raised when a destructive database operation targets a non-test database."""

    pass


def verify_database_is_disposable(engine: Engine) -> None:
    """Validate database identity before destructive test or teardown operations.

    Ensures that destructive operations (DROP TABLE, TRUNCATE, downgrade to base)
    can NEVER target the persistent research database.
    """
    db_name = engine.url.database or ""
    # Safe if SQLite in-memory or database explicitly designated as test
    is_safe = (
        engine.dialect.name == "sqlite" or "test" in db_name.lower() or db_name.endswith("_test")
    )

    if not is_safe or db_name == settings.POSTGRES_DB:
        raise DestructiveOperationBlockedError(
            f"DESTRUCTIVE_OPERATION_BLOCKED: Target database '{db_name}' is not an isolated test database. "
            "Destructive actions are strictly prohibited on the persistent research database."
        )


def get_engine(database_url: str | None = None) -> Engine:
    """Create a configured SQLAlchemy engine."""
    url = database_url or settings.DATABASE_URL
    is_sqlite = url.startswith("sqlite")

    engine_kwargs: dict[str, Any] = {
        "echo": False,
        "future": True,
    }

    if not is_sqlite:
        engine_kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 1800,
                "connect_args": {"connect_timeout": 1},
            }
        )

    logger.info("Initializing database engine (dialect: %s)", url.split(":")[0])
    return create_engine(url, **engine_kwargs)


_default_engine: Engine | None = None
_default_session_factory: sessionmaker[Session] | None = None

_test_engine: Engine | None = None
_test_session_factory: sessionmaker[Session] | None = None


def get_default_engine() -> Engine:
    """Retrieve or initialize singleton default database engine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = get_engine()
    return _default_engine


def get_test_engine() -> Engine:
    """Retrieve or initialize singleton test database engine."""
    global _test_engine
    if _test_engine is None:
        _test_engine = get_engine(settings.TEST_DATABASE_URL)
    return _test_engine


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Retrieve or create sessionmaker bound to engine."""
    global _default_session_factory, _test_session_factory
    eng = engine or get_default_engine()
    if eng.url.database == settings.POSTGRES_TEST_DB:
        if _test_session_factory is None:
            _test_session_factory = sessionmaker(
                bind=eng, autoflush=False, autocommit=False, expire_on_commit=False
            )
        return _test_session_factory

    if _default_session_factory is None or engine is not None:
        factory = sessionmaker(bind=eng, autoflush=False, autocommit=False, expire_on_commit=False)
        if engine is None:
            _default_session_factory = factory
        return factory
    return _default_session_factory


@contextmanager
def get_test_db_session() -> Generator[Session, None, None]:
    """Context manager for transactional test database sessions."""
    engine = get_test_engine()
    with get_db_session(engine) as session:
        yield session


@contextmanager
def get_db_session(engine: Engine | None = None) -> Generator[Session, None, None]:
    """Context manager for transactional database sessions.

    Automatically commits on normal exit and rolls back on exception.
    """
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("Database session transaction rolled back due to error: %s", exc)
        raise
    finally:
        session.close()


def check_database_connectivity(engine: Engine | None = None) -> dict[str, Any]:
    """Verify raw database connectivity and dialect information."""
    eng = engine or get_default_engine()
    with eng.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        server_version = conn.execute(
            text("SHOW server_version")
            if eng.dialect.name == "postgresql"
            else text("SELECT sqlite_version()")
        ).scalar()
        return {
            "status": "connected" if result == 1 else "unexpected_result",
            "dialect": eng.dialect.name,
            "driver": eng.driver,
            "server_version": str(server_version),
        }


def verify_postgis_extension(engine: Engine | None = None) -> dict[str, Any]:
    """Verify PostGIS extension presence and version."""
    eng = engine or get_default_engine()
    if eng.dialect.name != "postgresql":
        return {
            "postgis_installed": False,
            "version": None,
            "note": f"Dialect is {eng.dialect.name}; PostGIS requires PostgreSQL.",
        }

    with eng.connect() as conn:
        try:
            version = conn.execute(text("SELECT PostGIS_Full_Version()")).scalar()
            lib_version = conn.execute(text("SELECT PostGIS_Lib_Version()")).scalar()
            return {
                "postgis_installed": True,
                "version": str(lib_version),
                "full_version": str(version),
            }
        except Exception as exc:
            return {
                "postgis_installed": False,
                "error": str(exc),
                "note": "PostGIS extension not enabled or accessible in this database.",
            }


def get_table_counts(engine: Engine | None = None) -> dict[str, int]:
    """Report row counts across all canonical schema tables."""
    with get_db_session(engine) as session:
        return {
            "data_sources": session.query(func.count(DataSource.id)).scalar() or 0,
            "source_assets": session.query(func.count(SourceAsset.id)).scalar() or 0,
            "ingestion_runs": session.query(func.count(IngestionRun.id)).scalar() or 0,
            "storms": session.query(func.count(Storm.id)).scalar() or 0,
            "storm_aliases": session.query(func.count(StormAlias.id)).scalar() or 0,
            "track_observations": session.query(func.count(TrackObservation.id)).scalar() or 0,
            "data_quality_issues": session.query(func.count(DataQualityIssue.id)).scalar() or 0,
            "dataset_snapshots": session.query(func.count(DatasetSnapshot.id)).scalar() or 0,
            "satellite_products": session.query(func.count(SatelliteProduct.id)).scalar() or 0,
            "satellite_granules": session.query(func.count(SatelliteGranule.id)).scalar() or 0,
            "satellite_processed_crops": session.query(
                func.count(SatelliteProcessedCrop.id)
            ).scalar()
            or 0,
            "satellite_track_associations": session.query(
                func.count(SatelliteTrackAssociation.id)
            ).scalar()
            or 0,
        }


def audit_database_integrity(engine: Engine | None = None) -> dict[str, Any]:
    """Run an automated schema and constraint audit."""
    eng = engine or get_default_engine()
    conn_info = check_database_connectivity(eng)
    postgis_info = verify_postgis_extension(eng)
    counts = get_table_counts(eng)

    return {
        "connectivity": conn_info,
        "postgis": postgis_info,
        "table_counts": counts,
        "schema_tables": [
            DataSource.__tablename__,
            SourceAsset.__tablename__,
            IngestionRun.__tablename__,
            Storm.__tablename__,
            StormAlias.__tablename__,
            TrackObservation.__tablename__,
            DataQualityIssue.__tablename__,
            DatasetSnapshot.__tablename__,
            SatelliteProduct.__tablename__,
            SatelliteGranule.__tablename__,
            SatelliteProcessedCrop.__tablename__,
            SatelliteTrackAssociation.__tablename__,
        ],
    }
