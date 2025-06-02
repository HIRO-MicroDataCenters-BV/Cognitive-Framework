"""
This module contains fixtures for the FastAPI application tests.
"""

import os
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./unittest.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
BASE_PATH = os.getenv("BASE_PATH", "/cogapi")
Base.metadata.create_all(bind=engine)


def override_get_db():
    """
    Provide a database session for testing.

    Yields:
        SQLAlchemy session: The database session for testing.
    """
    try:
        db_app = TestingSessionLocal()
        yield db_app
    finally:
        db_app.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class PrefixedTestClient(TestClient):
    """
    Test client with a URL prefix.
    """

    def __init__(self, app: object, prefix: str) -> None:
        """
        Initialize the test client with a URL prefix.
        Args:
            app: object
            prefix: str
        """
        super().__init__(app)
        self.prefix = prefix

    def _add_prefix(self, url: str) -> str:
        """
        Add the prefix to the URL.
        Args:
            url: str

        Returns:

        """
        return f"{self.prefix}{url}"

    def get(self, url: str, **kwargs: Dict[str, Any]) -> Any:
        """
        Make a GET request with the URL prefix.
        Args:
            url: str
            **kwargs: dict[str, object]

        Returns:

        """
        return super().get(self._add_prefix(url), **kwargs)

    def post(self, url: str, **kwargs: Dict[str, Any]) -> Any:
        """
        Make a POST request with the URL prefix.
        Args:
            url: str
            **kwargs: dict[str, object]

        Returns:

        """
        return super().post(self._add_prefix(url), **kwargs)

    def put(self, url: str, **kwargs: Dict[str, Any]) -> Any:
        """
        Make a PUT request with the URL prefix.
        Args:
            url: str
            **kwargs: dict[str, object]

        Returns:

        """
        return super().put(self._add_prefix(url), **kwargs)

    def delete(self, url: str, **kwargs: Dict[str, Any]) -> Any:
        """
        Make a DELETE request with the URL prefix.
        Args:
            url: str
            **kwargs: dict[str, object]

        Returns:

        """
        return super().delete(self._add_prefix(url), **kwargs)

    def patch(self, url: str, **kwargs: Dict[str, Any]) -> Any:
        """
        Make a PATCH request with the URL prefix.
        Args:
            url: str
            **kwargs: dict[str, object]

        Returns:

        """
        return super().patch(self._add_prefix(url), **kwargs)


@pytest.fixture(scope="module")
def test_client():
    """
    Fixture to provide a test client for the FastAPI application.
    Returns:

    """
    client = PrefixedTestClient(app, BASE_PATH)
    yield client


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    """
    Setup and teardown function to clean up the test database after tests.
    """
    yield
    db_app = TestingSessionLocal()
    try:
        db_app.close()
    finally:
        if os.path.exists("unittest.db"):
            os.remove("unittest.db")


@pytest.fixture
def mock_getenv():
    """
    Fixture to mock `os.getenv` with predefined environment variables.
    """
    env_vars = {
        "MLFLOW_S3_ENDPOINT_URL": "http://127.0.0.1:9000",
        "AWS_ACCESS_KEY_ID": "minio",
        "AWS_SECRET_ACCESS_KEY": "minio123",
        "API_BASEPATH": "http://randomn",
        "CONFIG_TYPE": "config.app_config.TestingConfig",
        "DB_NAME": "cognitivedb",
        "DB_PASSWORD": "hiropwd",
        "DB_PORT": "5432",
        "DB_USER": "hiro",
    }

    def mock_env(key, default=None):
        return env_vars.get(key, default)

    with patch("os.getenv", side_effect=mock_env):
        yield
