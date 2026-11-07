import os
import sys

# Ensure Windows Defender Application Control / AppLocker environments run smoothly
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from vayumarg.core.config import settings
from vayumarg.database.schema import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from environment override or central settings
target_db_url = os.getenv("ALEMBIC_DB_URL") or settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", target_db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    target_url = os.getenv("ALEMBIC_DB_URL") or settings.DATABASE_URL
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = target_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
