from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import tasks.models  # noqa: F401  (register tables)
import users.models  # noqa: F401
from core.database import Base

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_should_match_orm_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'schema.db'}"
    command.upgrade(alembic_config(url), "head")
    with create_engine(url).connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []


def test_migrations_should_downgrade_to_empty_schema(tmp_path):
    url = f"sqlite:///{tmp_path / 'schema.db'}"
    config = alembic_config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert inspect(create_engine(url)).get_table_names() == ["alembic_version"]
