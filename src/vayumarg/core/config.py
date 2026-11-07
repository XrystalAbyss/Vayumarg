"""Application configuration management for Vayumarg.

Loaded from environment variables and .env file with validation.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Vayumarg central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL / PostGIS Settings
    POSTGRES_USER: str = "vayumarg_user"
    POSTGRES_PASSWORD: str = "vayumarg_dev_password"
    POSTGRES_DB: str = "vayumarg"
    POSTGRES_TEST_DB: str = "vayumarg_test"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5433

    # Canonical Database Connection URL (Persistent Research / Dev)
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://vayumarg_user:vayumarg_dev_password@127.0.0.1:5433/vayumarg",
        description="Canonical PostgreSQL/PostGIS connection URL.",
    )

    # Isolated Test Database Connection URL (Strictly for automated integration tests)
    TEST_DATABASE_URL: str = Field(
        default="postgresql+psycopg://vayumarg_user:vayumarg_dev_password@127.0.0.1:5433/vayumarg_test",
        description="Isolated PostgreSQL/PostGIS test database URL.",
    )

    # Lightweight Fallback Database URL (for Docker-unavailable or isolated unit test environments)
    FALLBACK_DATABASE_URL: str = Field(
        default="sqlite:///data/interim/vayumarg_fallback.sqlite3",
        description="Fallback SQLite database URL.",
    )

    # PostGIS strict requirement flag
    REQUIRE_POSTGIS: bool = True

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = Path("./data")
    MANIFEST_DIR: Path = Path("./data/manifests")

    def get_data_dir(self, subdir: str = "") -> Path:
        """Resolve and ensure existence of data subdirectories."""
        target = self.BASE_DIR / self.DATA_DIR / subdir
        target.mkdir(parents=True, exist_ok=True)
        return target


settings = Settings()
