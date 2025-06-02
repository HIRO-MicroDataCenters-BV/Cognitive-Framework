"""
test_migrations module
"""
import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from app.db.session import Base


@pytest.fixture
def sqlite_memory_engine():
    """Creates a unique SQLite in-memory database engine."""
    test_id = "test_db_1"  # Replace with dynamic ID generation if needed
    database_url = f"sqlite:///{test_id}?mode=memory&cache=shared"
    engine = create_engine(database_url, connect_args={"uri": True})
    yield engine
    engine.dispose()
    os.remove(test_id)


@pytest.fixture
def alembic_config(sqlite_memory_engine):
    """Provides an Alembic configuration object for the test database."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", str(sqlite_memory_engine.url))
    return config


@pytest.fixture
def setup_database(alembic_config):
    """Applies all migrations to the SQLite in-memory database."""
    command.upgrade(alembic_config, "head")
    yield
    command.downgrade(alembic_config, "base")


@pytest.fixture
def test_session(sqlite_memory_engine, setup_database):
    """Provides a session for interacting with the database."""
    session = sessionmaker(bind=sqlite_memory_engine)
    session = session()
    yield session
    session.close()


def test_database_creation(sqlite_memory_engine):
    """Test the creation of the database."""
    Base.metadata.create_all(sqlite_memory_engine)
    inspector = inspect(sqlite_memory_engine)
    tables = inspector.get_table_names()
    assert "model_info" in tables
    assert "experiments" in tables
    assert "run_details" in tables
    assert "tasks" in tables


def test_migration_upgrade(alembic_config, sqlite_memory_engine):
    """Test applying the latest migration."""
    command.upgrade(alembic_config, "969bb48172d7")  # Apply initial migration
    command.upgrade(alembic_config, "813d2c88b0c4")  # Apply broker_details migration
    inspector = inspect(sqlite_memory_engine)
    tables = inspector.get_table_names()
    assert "broker_details" in tables
    assert "model_info" in tables
    assert "experiments" in tables
    assert "run_details" in tables
