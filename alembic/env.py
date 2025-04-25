import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy import engine_from_config
from src.database import Base, engine  # Import engine from your database file
from src.models import *
from alembic import context

# Alembic Config object, which provides access to the .ini file
config = context.config

# Setup logging from the Alembic configuration file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define target metadata for autogeneration of migrations
target_metadata = Base.metadata

# Function to run migrations in offline mode (without a live connection)
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode. This configures the context with just a URL and not an Engine."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# Function to run migrations in online mode (with a live connection)
def run_migrations_online() -> None:
    """Run migrations in 'online' mode. This scenario requires an Engine."""
    connectable = engine  # Use the pre-configured engine directly

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# Execute migrations in offline or online mode depending on the configuration
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
