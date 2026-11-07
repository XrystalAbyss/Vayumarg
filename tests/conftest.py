"""Shared pytest configuration and test fixtures for Vayumarg.

Sets up environment, ensures C-extension bypass for WDAC,
and provides synthetic test fixtures strictly labeled as synthetic.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

# Set environment bypass for Windows Defender Application Control
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from vayumarg.database.engine import (
    get_db_session,
    get_test_engine,
    verify_database_is_disposable,
)
from vayumarg.database.schema import (
    DataSource,
    SourceAsset,
    Storm,
)


@pytest.fixture(scope="session")
def db_engine():
    """Retrieve isolated test database engine and verify safety."""
    engine = get_test_engine()
    # Explicit safety guarantee: integration tests must only target test databases
    verify_database_is_disposable(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a transactional database session rolled back after test."""
    with get_db_session(db_engine) as session:
        yield session
        session.rollback()


@pytest.fixture(scope="function")
def synthetic_data_source(db_session: Session) -> DataSource:
    """Fixture providing a verified synthetic data source."""
    ds = DataSource(
        id=uuid.uuid4(),
        provider_name="SYNTHETIC_IMD",
        dataset_name="SYNTHETIC_BEST_TRACK_NIO",
        version="v1.0-synthetic",
        citation="Synthetic test data strictly for F0 schema verification",
        license="CC-BY-4.0-Testing",
        created_at_utc=datetime.now(UTC),
    )
    db_session.add(ds)
    db_session.flush()
    return ds


@pytest.fixture(scope="function")
def synthetic_source_asset(db_session: Session, synthetic_data_source: DataSource) -> SourceAsset:
    """Fixture providing a synthetic source asset with valid SHA-256."""
    asset = SourceAsset(
        id=uuid.uuid4(),
        data_source_id=synthetic_data_source.id,
        artifact_uri="file:///synthetic/data/raw/synthetic_cyclone_2024.csv",
        sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=1048576,
        asset_type="TRACK_CSV",
        retrieval_time_utc=datetime.now(UTC),
        asset_metadata={"is_synthetic_fixture": True},
    )
    db_session.add(asset)
    db_session.flush()
    return asset


@pytest.fixture(scope="function")
def synthetic_storm(db_session: Session) -> Storm:
    """Fixture providing a synthetic cyclone storm record."""
    storm = Storm(
        id=uuid.uuid4(),
        canonical_name="SYNTHETIC_AMPHAN_TEST",
        season_year=2024,
        primary_basin="BOB",
        nature="TS",
        created_at_utc=datetime.now(UTC),
    )
    db_session.add(storm)
    db_session.flush()
    return storm
