"""Unit tests for configuration loading and validation."""

import pytest

from vayumarg.core.config import Settings


@pytest.mark.unit
def test_default_settings():
    """Verify default settings instantiation and types."""
    settings = Settings()
    assert settings.POSTGRES_DB == "vayumarg"
    assert settings.POSTGRES_PORT == 5433
    assert "postgresql+psycopg://" in settings.DATABASE_URL
    assert settings.REQUIRE_POSTGIS is True


@pytest.mark.unit
def test_data_dir_resolution(tmp_path):
    """Verify data subdirectory creation and path resolution."""
    settings = Settings(DATA_DIR=tmp_path)
    raw_dir = settings.get_data_dir("raw")
    assert raw_dir.is_dir()
    assert raw_dir.name == "raw"
