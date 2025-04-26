# import os
# from logging.config import fileConfig 
# from src.database import Base, engine   
# from src.models import *
# from alembic import context

# config = context.config

# # Setup logging from the Alembic configuration file
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # Define target metadata for autogeneration of migrations
# target_metadata = Base.metadata

# # Function to run migrations in offline mode (without a live connection)
# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode. This configures the context with just a URL and not an Engine."""
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )

#     with context.begin_transaction():
#         context.run_migrations()

# # Function to run migrations in online mode (with a live connection)
# async def run_migrations_online() -> None:
#     """Run migrations in 'online' mode. This scenario requires an Engine."""
#     connectable = engine  # Use the pre-configured engine directly

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection,
#             target_metadata=target_metadata
#         )

#         with context.begin_transaction():
#             context.run_migrations()

# # Execute migrations in offline or online mode depending on the configuration
# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()


import os
import asyncio
from logging.config import fileConfig
from alembic import context
from src.database import Base, engine
from src.models import *

config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define target metadata
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

async def run_async_migrations() -> None:
    """Run async migrations."""
    async with engine.connect() as connection:
        # Configure the context with sync connection
        def do_run_migrations(conn):
            context.configure(
                connection=conn,
                target_metadata=target_metadata
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()