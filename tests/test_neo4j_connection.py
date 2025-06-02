"""
Test cases for neo4j connection
"""
from unittest.mock import patch, MagicMock
import pytest
from app.db.neo4j_connection import Neo4jConnection


@pytest.fixture
def neo4j_connection():
    """
    Fixture to create a Neo4jConnection instance for testing.
    """
    with patch("app.db.neo4j_connection.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MagicMock()
        conn = Neo4jConnection(
            uri="bolt://localhost:7687", user="neo4j", password="password"
        )
        yield conn
        conn.close()


def test_neo4j_connection_init(neo4j_connection):
    """
    Test the initialization of the Neo4jConnection.
    """
    assert neo4j_connection._driver is not None


def test_neo4j_connection_close(neo4j_connection):
    """
    Test the closing of the Neo4jConnection.
    """
    neo4j_connection.close()
    neo4j_connection._driver.close.assert_called_once()


def test_neo4j_connection_query(neo4j_connection):
    """
    Test the query method of the Neo4jConnection.
    """
    mock_session = MagicMock()
    mock_run = MagicMock()
    mock_run.return_value = [MagicMock(data=lambda: {"key": "value"})]
    mock_session.run = mock_run
    neo4j_connection._driver.session.return_value.__enter__.return_value = mock_session

    result = neo4j_connection.query("MATCH (n) RETURN n")
    assert result == [{"key": "value"}]
    mock_session.run.assert_called_once_with("MATCH (n) RETURN n", {})
