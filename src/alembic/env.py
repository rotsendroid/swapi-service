import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from api.config.settings import get_settings
from api.storage.postgres import Base

# Import all models and associations for Alembic to detect them
from api.domains.characters.models import Character  # noqa: F401
from api.domains.films.models import Film  # noqa: F401
from api.domains.starships.models import Starship  # noqa: F401
from api.domains import associations  # noqa: F401

settings = get_settings()
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_section_option("alembic", "sqlalchemy.url", settings.postgres_url)
engine = create_async_engine(settings.postgres_url, echo=True)


async def run_migrations_online():
    """Run migrations in an async environment."""
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)  # type: ignore


def do_run_migrations(connection):  # type: ignore
    """Helper function to run migrations synchronously inside an async connection."""
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore
    with context.begin_transaction():
        context.run_migrations()


# Ensure the async function is executed properly
if context.is_offline_mode():
    context.configure(url=settings.postgres_url, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_migrations_online())
